import base64
import os
import logging
import sys
from urllib.parse import quote_plus
from pymongo import MongoClient
import time
from dotenv import load_dotenv
import pandas as pd
from typing import List, Dict, Optional
from tqdm import tqdm
import openai
import anthropic
import faiss
import json
from datetime import datetime
import numpy as np
import re
import requests
import io
from PIL import Image

from meta import FacebookScraper
from Logging import LoggingManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ads_pipeline.log'),
        logging.StreamHandler()
    ]
)

class AdsPipeline:
    def __init__(self, openai_api_key: str = None, anthropic_api_key: str = None, mongo_uri: str = None, keywords_file: str = 'skincare_keywords.csv', use_proxy: bool = True, verbose: bool = False):
        self.logger = LoggingManager.setup_logging(verbose=verbose)
        self.scraper = FacebookScraper(use_proxy=use_proxy)

        self.openai = openai
        if openai_api_key:
            self.openai.api_key = openai_api_key
        elif os.getenv("OPENAI_API_KEY"):
            self.openai.api_key = os.getenv("OPENAI_API_KEY")
        else:
            raise ValueError("OpenAI API key must be provided either through constructor or OPENAI_API_KEY environment variable")
        
        if anthropic_api_key:
            self.claude = anthropic.Anthropic(
                api_key=anthropic_api_key,
            )
        elif os.getenv("ANTHROPIC_API_KEY"):
            self.claude = anthropic.Anthropic(
                api_key=os.getenv("ANTHROPIC_API_KEY"),
            )
        else:
            raise ValueError("ANTHROPIC API key must be provided either through constructor or ANTHROPIC_API_KEY environment variable")
        
        if mongo_uri:
            self.mongo_uri = mongo_uri
        elif os.getenv("MONGO_URI"):
            self.mongo_uri = os.getenv("MONGO_URI")
        else:
            raise ValueError("Mongo URI must be provided either through constructor or MONGO_URI environment variable")
        self.client = MongoClient(self.mongo_uri)
        self.db = self.client["main"]
        self.collection = self.db["meta-ads-backup"]
            
        self.keywords_file = keywords_file

        self.full_ads = [] 
        self.processed_ads = []
        
        self.dimension = 1536
        try:
            self.index = faiss.read_index("skincare_ads.index")
            with open("ad_ids.json", "r") as f:
                self.ad_ids = json.load(f)
            self.logger.info(f"Loaded existing index with {self.index.ntotal} vectors")
        except:
            self.index = faiss.IndexFlatL2(self.dimension)
            self.ad_ids = []
            self.logger.info("Created new FAISS index")

    def read_keywords_from_csv(self) -> List[Dict]:
        """Read keywords and their metadata from CSV file"""
        try:
            df = pd.read_csv(self.keywords_file)
            required_columns = ['Keyword', 'Category', 'Search Intent']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                logging.error(f"Missing required columns: {missing_columns}")
                return []
            
            keywords_data = df.to_dict('records')
            self.logger.info(f"Loaded {len(keywords_data)} keywords from {self.keywords_file}")
            return keywords_data
            
        except Exception as e:
            logging.error(f"Error reading keywords file: {str(e)}")
            return []

    def collect_ads(self, keywords_data: List[Dict]):
        pages = []
        for keyword_info in tqdm(keywords_data, desc="Searching pages"):
            try:
                results = self.scraper.search_pages(query=keyword_info['Keyword'])
                for page in results:
                    page['keyword_info'] = keyword_info
                    pages.append(page)
            except:
                self.logger.error(f"Error searching pages for {keyword_info['Keyword']}: {str(e)}")
                continue

        self.logger.info(f"Found {len(pages)} pages to process")

        for page in tqdm(pages, desc='Collecting Ads'):
            try:
                page_id = page['page_id']
                has_next_page = True
                cursor = None
                while has_next_page:
                    ads = self.scraper.get_page_ads(page_id=page_id,active=False,country=['IN'],limit=30,cursor=cursor)
                    next_page = ads['data']['ad_library_main']['search_results_connection']['page_info']
                    cursor = next_page['end_cursor']
                    has_next_page = next_page['has_next_page']

                    self.full_ads.extend(ads['data']['ad_library_main']['search_results_connection']['edges'])
                    logging.info(f'Got {len(ads)}')
                    break
            except Exception as e:
                self.logger.error(f"Error collecting ads: {str(e)}")

        self.logger.info(f"Successfully collected {len(self.full_ads)} ads")
        return self.full_ads

    def clean_data(self, ad):
        """Clean invalid characters in ad data."""
        if isinstance(ad, str):
            return ad.encode('utf-8', 'replace').decode('utf-8')
        elif isinstance(ad, dict):
            return {k: self.clean_data(v) for k, v in ad.items()}
        elif isinstance(ad, list):
            return [self.clean_data(item) for item in ad]
        return ad

    def push_to_mongo(self):
        """Push data to MongoDB"""
        try:
            self.processed_ads = [self.clean_data(ad) for ad in tqdm(self.processed_ads, desc='Cleaning ads')]
            self.logger.debug(f"Pushing {len(self.processed_ads)} ads to MongoDB")
            self.collection.insert_many(self.processed_ads)
            self.logger.info(f"Stored {len(self.processed_ads)} ads to MongoDB")
        except Exception as e:
            self.logger.error(f"MongoDB error: {e}")

    def _compress_media(self, content, max_size_mb=5):
        """ Compress media to fit within size limit """
        try:
            image = Image.open(io.BytesIO(content))
            
            compression_qualities = [85, 75, 65, 50]
            for quality in compression_qualities:
                buffer = io.BytesIO()
                image.save(buffer, format='JPEG', quality=quality)
                compressed_content = buffer.getvalue()
                
                if len(compressed_content) <= max_size_mb * 1024 * 1024:
                    base64_data = base64.b64encode(compressed_content).decode('utf-8')
                    return base64_data, 'image/jpeg'
            
            base_width = image.width
            while base_width > 100:
                base_width = int(base_width * 0.8)
                resized_image = image.resize(
                    (base_width, int(base_width * image.height / image.width)), 
                    Image.LANCZOS
                )
                
                buffer = io.BytesIO()
                resized_image.save(buffer, format='JPEG', quality=65)
                compressed_content = buffer.getvalue()
                
                if len(compressed_content) <= max_size_mb * 1024 * 1024:
                    base64_data = base64.b64encode(compressed_content).decode('utf-8')
                    return base64_data, 'image/jpeg'
        
        except Exception as e:
            self.logger.debug(f"Error compressing media: {e}")
            return None, None

    def prepare_media_from_url(self, url, max_size_mb=5):
        """ Download and prepare media from a URL for Claude API """
        if not url or url in ["Not Available", ""]:
            return None, None
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            media_type = response.headers.get('Content-Type', '')
            
            if len(response.content) > max_size_mb * 1024 * 1024:
                return self._compress_media(response.content, media_type, max_size_mb)
            
            base64_data = base64.b64encode(response.content).decode('utf-8')
            return base64_data, media_type
        
        except requests.RequestException as e:
            self.logger.debug(f"Error downloading media: {e}")
            return None, None

    def get_company_description(self, company_name: str) -> str:
        """Get company description using OpenAI"""
        prompt = f"""
        Describe {company_name} as a skincare/beauty-related entity. Include the following details:
        - A brief history or background.
        - Its target audience or market.
        - Key products or services offered, if applicable.
        - Its market positioning or role in the beauty industry.
        - The core values, philosophy, or principles it upholds.
        If {company_name} refers to a person, concept, or something other than a company, and you are not sure about the answer just return "Entity Unknown".
        Keep the response concise and limited to 100 words.
        """
        
        response = self.openai.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.choices[0].message.content.strip()

    def enrich_ad_data(self, ad: Dict, ad_creative: base64, media_type: str, keyword_info: str) -> Dict:
        """Enrich ad data with additional analysis, considering keyword metadata"""
        
        prompt = f"""
        Analyze the following skincare advertisement and its creative content in relation to the search keyword: {keyword_info}. Provide a structured evaluation that includes:

        - The main features of the product being advertised.
        - Visual elements analysis (imagery, colors, layout, text overlays).
        - How the visual content supports the marketing message.
        - How well the ad's target audience aligns with the search intent implied by the keyword.
        - The key benefits of the product as emphasized in both text and visuals.
        - Pricing information, including its positioning (e.g., affordable, premium) if mentioned.
        - The marketing strategy or angle employed to appeal to potential customers.
        - The relevance of both the advertisement's content and visuals to the specified search keyword.
        
        Ad Content:
        {ad}

        Analyze both the text content above and the provided image/video (if available) to give a comprehensive evaluation.
        Ensure your analysis is concise, actionable, and aligned with the perspective of enhancing advertising effectiveness.
        Provide your answer within <answer> tags.
        """

        try:

            if media_type == "IMAGE" and ad_creative:
                message = self.claude.messages.create(
                    model="claude-3-5-sonnet-20240620",
                    max_tokens=8192,
                    temperature=0,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": prompt
                                },
                                {
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": "image/jpeg",
                                        "data": ad_creative
                                    }
                                }
                            ]
                        }
                    ],
                    extra_headers={
                        "anthropic-beta": "max-tokens-3-5-sonnet-2024-07-15"
                    }
                )
            else:
                message = self.claude.messages.create(
                    model="claude-3-5-sonnet-20240620",
                    max_tokens=8192,
                    temperature=0,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": prompt
                                }
                            ]
                        }
                    ],
                    extra_headers={
                        "anthropic-beta": "max-tokens-3-5-sonnet-2024-07-15"
                    }
                )
            
            # response = self.openai.chat.completions.create(
            #     model="gpt-4",
            #     messages=[{"role": "user", "content": prompt}]
            # )
            
            # return response.choices[0].message.content.strip()

            res = str(message.content[0])
            pattern = r"<answer>(.*?)</answer>"
            match = re.search(pattern, res, re.DOTALL)
            res = match.group(1).strip()

        except Exception as e:
            self.logger.debug(f"Error enriching ad - {e}")

        return res

    def get_embedding(self, text: str) -> List[float]:
        """Get embedding for text"""
        try:
            text = self.clean_data(text)
            # OpenAI Embedding
            response = self.openai.embeddings.create(
                model="text-embedding-ada-002",
                input=text
            )
        except Exception as e:
            self.logger.debug(f"Error getting embedding - {e}")
            return None
        
        # Claude Embedding
        # response = self.claude.messages.create(
        #     model="claude-3-5-sonnet-20240620",
        #     max_tokens=1024,
        #     system="Please generate an embedding for the following text.",
        #     messages=[
        #         {"role": "user", "content": f"Generate embedding for: {text}"}
        #     ]
        # )

        # return response.content[0].text
        return response.data[0].embedding
    
    def process_and_store(self) -> List[Dict]:
        """Helper method to process a single ad"""
        try:
            all_embeddings = []
            for page in tqdm(self.full_ads, desc='Processing ads'):
                page_data = page['node']["collated_results"][0]
                company_desc = self.get_company_description(page_data['page_name'])
                try:
                    media_type = page_data.get('snapshot', {}).get('display_format', "")
                    if media_type == "IMAGE":
                        try:
                            image_url = page_data.get('snapshot', {}).get('images', [{'original_image_url': "Not Available"}])[0]['original_image_url']
                        except:
                            image_url = "Not Available"
                        ad_creative, _ = self.prepare_media_from_url(image_url)
                    else:
                        ad_creative = None
                    enriched_ad = self.enrich_ad_data(page_data.get('snapshot', {}), ad_creative, media_type, page_data.get('keyword_info', "skincare"))
                    ad_text = f"{page_data.get('snapshot', {}).get('title', "")} {page_data.get('snapshot', {}).get('body', {}).get('text', "")} {enriched_ad}"
                    embedding = self.get_embedding(ad_text)
                    if embedding:
                        all_embeddings.append(embedding)
                        self.ad_ids.append(page_data.get('ad_archive_id', ""))
                except Exception as e:
                    self.logger.debug(f"Error processing ad: {str(e)}")
                    continue

                ad_info = {
                    'ad_id': page_data.get('ad_archive_id', ""),
                    'title': page_data.get('snapshot', {}).get('title', ""),
                    'body': page_data.get('snapshot', {}).get('body', {}).get('text', ""),
                    'cta_text': page_data.get('snapshot', {}).get('cta_text', ""),
                    'cta_type': page_data.get('snapshot', {}).get('cta_type', ""),
                    'caption': page_data.get('snapshot', {}).get('caption', {}),
                    'display_format': page_data.get('snapshot', {}).get('display_format', ""),
                    'link_description': page_data.get('snapshot', {}).get('link_description', ""),
                    'link_url': page_data.get('snapshot', {}).get('link_url', ""),
                    'images': page_data.get('snapshot', {}).get('images', []),
                    'videos': page_data.get('snapshot', {}).get('videos', []),
                    'start_date': page_data.get('start_date', None),
                    'end_date': page_data.get('end_date', None),
                    'total_active_time': page_data.get('total_active_time', None),
                    'spend': page_data.get('spend', None),
                }

                advertiser_info = {
                    'page_id': page_data.get('snapshot', {}).get('page_id', ""),
                    'page_name': page_data.get('snapshot', {}).get('page_name', ""),
                    'page_profile_picture_url': page_data.get('snapshot', {}).get('page_profile_picture_url', ""),
                    'page_profile_uri': page_data.get('snapshot', {}).get('page_profile_uri', ""),
                    'page_categories': page_data.get('snapshot', {}).get('page_categories', []),
                    'page_like_count': page_data.get('snapshot', {}).get('page_like_count', 0),
                    'country_iso_code': page_data.get('snapshot', {}).get('country_iso_code', None),
                }

                res = {
                    'ad_id': page_data.get('ad_archive_id', ""),
                    'keyword_info': page_data.get('keyword_info', {}),
                    'ad_info': ad_info,
                    'advertiser_info': advertiser_info,
                    'company_description': company_desc,
                    'enriched_data': enriched_ad,
                    'processed_at': datetime.now().isoformat()
                }
                
                self.processed_ads.append(res)
                
            self.push_to_mongo()

            if all_embeddings:
                embeddings_array = np.array(all_embeddings).astype('float32')
                self.index.add(embeddings_array)
            
            faiss.write_index(self.index, "skincare_ads.index")
            with open("ad_ids.json", "w") as f:
                json.dump(self.ad_ids, f)
                
            self.logger.info("Data processing and storage complete")
            return self.processed_ads
        except Exception as e:
            self.logger.error(f"Error processing page: {str(e)}")
            return []
        
    def search_ads(self, query: str, k: int = 10) -> List[Dict]:
        """Search for relevant ads using query"""

        if self.index.ntotal == 0:
            self.logger.warning("Index is empty. Please build the index first.")
            return []
    
        query_embedding = self.get_embedding(query)
        
        search_k = k * 2
        
        D, I = self.index.search(np.array([query_embedding]), search_k)
        
        with open("ad_ids.json", "r") as f:
            ad_ids = json.load(f)

        seen = set()
        retrieved_ad_ids = []
        for idx in I[0]:
            if idx >= 0 and idx < len(ad_ids):
                ad_id = ad_ids[idx]
                if ad_id not in seen:
                    seen.add(ad_id)
                    retrieved_ad_ids.append(ad_id)
            if len(retrieved_ad_ids) == k:
                break

        mongo_results = list(self.collection.find({'ad_id': {'$in': retrieved_ad_ids}}))
        
        results = []
        for ad in mongo_results:
            ad_id = ad['ad_id']
            try:
                index = retrieved_ad_ids.index(ad_id)
                relevance_score = float(D[0][index])
                ad['relevance_score'] = relevance_score
                results.append(ad)
            except ValueError:
                continue
        
        results.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        return results
            
def main():
    load_dotenv()
        
    mongo_uri = os.getenv("MONGO_URI")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        
    pipeline = AdsPipeline(
        openai_api_key=openai_api_key,
        anthropic_api_key=anthropic_api_key,
        mongo_uri=mongo_uri,
        keywords_file='skincare_keywords.csv',
        use_proxy=True,
        verbose=False
    )

    keywords_data = pipeline.read_keywords_from_csv()
    if not keywords_data:
        logging.error("No keywords found. Please check your CSV file.")
        return
    
    ads = pipeline.collect_ads(keywords_data=keywords_data)
    processed_ads = pipeline.process_and_store()

    # search_results = pipeline.search_ads(query="best skin care products")
    # print(len(search_results))

if __name__ == "__main__":
    main() 