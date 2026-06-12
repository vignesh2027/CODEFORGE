import os

from langchain_tavily import TavilySearch

from config.settings import TAVILY_API_KEY

os.environ["TAVILY_API_KEY"] = TAVILY_API_KEY

search_tool = TavilySearch(max_results=5)
