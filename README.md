![Twospoon Banner](assets/banner.png)

# Meta Ads Pipeline

A sophisticated pipeline for collecting, analyzing, and processing Meta (Facebook) ads data with a focus on skincare/beauty industry advertisements. The pipeline uses AI-powered analysis, vector embeddings, and efficient data storage for advanced ad insights.

## Features

- **Interactive Dashboard**: Streamlit-based frontend for easy ad searching and visualization
- **Automated Ad Collection**: Scrapes Meta Ads Library using proxy support
- **AI-Powered Analysis**: Utilizes both OpenAI (GPT-4) and Anthropic (Claude) for deep ad content analysis
- **Vector Search**: Implements FAISS for efficient similarity-based ad searching
- **Media Processing**: Handles image compression and processing
- **Data Enrichment**: Adds company descriptions and detailed ad analysis
- **MongoDB Integration**: Stores processed data in a structured format
- **Keyword-Based Targeting**: Uses CSV-based keyword configuration

## Prerequisites

- Python 3.8+
- MongoDB instance
- OpenAI API key
- Anthropic API key
- Valid proxy configuration (optional but recommended)
- Streamlit

## Installation

1. Clone the repository:

```bash
git clone https://github.com/AdvaySanketi/Meta-Ads-Project
cd meta-ads-pipeline
```

2. Install required packages:

```bash
pip install -r requirements.txt
```

3. Set up environment variables in `.env`:

```env
MONGO_URI=your_mongodb_uri
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
PROXY_USERNAME=your_proxy_username
PROXY_PWD=your_proxy_password
PROXY_DOMAIN=your_proxy_domain
PROXY_PORT=your_proxy_port
```

4. Add your keywords CSV file with the following columns:
   - Keyword
   - Category
   - Search Intent
     or use the default skincare_keywords.csv file provided in the repository

## Usage

### Running the Dashboard

1. Start the Streamlit app:

```bash
streamlit run streamlit_app.py
```

2. Open your browser and navigate to the displayed URL (typically `http://localhost:8501`)

3. Use the search bar to find relevant ads based on your query

### Using the Pipeline API

```python
from ads_pipeline import AdsPipeline

pipeline = AdsPipeline(
    openai_api_key=openai_api_key,
    anthropic_api_key=anthropic_api_key,
    mongo_uri=mongo_uri,
    keywords_file='skincare_keywords.csv',
    use_proxy=True,
    verbose=False
)

# Read keywords and collect ads
keywords_data = pipeline.read_keywords_from_csv()
ads = pipeline.collect_ads(keywords_data=keywords_data)

# Process and store ads
processed_ads = pipeline.process_and_store()

# Search for relevant ads
results = pipeline.search_ads(query="best skin care products", k=10)
```

## Key Components

### Frontend (Streamlit Dashboard)

- Search interface for ad discovery
- Detailed ad cards with images/videos
- Expandable sections for additional information
- Metrics visualization
- Responsive grid layout

### Backend (AdsPipeline)

- Initializes connections to OpenAI, Claude, and MongoDB
- Manages FAISS index for vector search
- Handles ad collection and processing

## Known Issues & TODO

1. **Search Functionality**:

   - Search results sometimes include duplicate ads
   - Need to implement pagination for large result sets

2. **Performance**:

   - Initial loading of ads can be slow
   - Memory usage optimization needed for large datasets

3. **UI/UX**:

   - Need to add sorting and filtering options

4. **Data Collection**:
   - Proxy handling needs improvement (Apply Token Bucket Algorithm)
   - Rate limiting issues with Meta's API
   - Need better error recovery for failed scraping attempts

## Data Structure

Processed ads contain:

- Ad content and creative details
- Advertiser information
- AI-generated analysis and insights
- Company description
- Keyword metadata
- Vector embeddings for similarity search

## Error Handling

The pipeline includes:

- Comprehensive logging
- Error recovery mechanisms
- Data validation
- Proxy failure handling (Not Complete)
- API rate limiting management

## Contributing

Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any contributions you make are greatly appreciated.

1. Fork the project.
2. Create your feature branch:
   ```bash
   git checkout -b feature/AmazingFeature
   ```
3. Commit your changes:
   ```bash
   git commit -m 'Add some Amazing Feature'
   ```
4. Push to the branch:
   ```bash
   git push origin feature/AmazingFeature
   ```
5. Open a pull request.

## License

Distributed under the MIT License. See [LICENSE](LICENSE) for more information.

## Support

Having trouble? Want to request a feature? Here's how you can get help:

- Open an issue.
- Contact the maintainer: [**Advay Sanketi**](mailto:advay2807@gmail.com) / [**Santosh Bishnoi**](mailto:santosh@twospoon.ai)
