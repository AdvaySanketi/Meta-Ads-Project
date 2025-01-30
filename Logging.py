import logging


class LoggingManager:
    """Manages logging configuration"""
    
    @staticmethod
    def setup_logging(verbose: bool = False, log_file: str = 'ads_pipeline.log'):
        """Setup logging with configurable verbosity"""
        level = logging.DEBUG if verbose else logging.INFO
        
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
            if verbose else
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        
        logging.getLogger().handlers.clear()
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        logger = logging.getLogger()
        logger.setLevel(level)
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger