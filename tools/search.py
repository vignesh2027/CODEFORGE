import os

from langchain_community.tools.tavily_search import TavilySearchResults

from config.settings import TAVILY_API_KEY

os.environ["TAVILY_API_KEY"] = TAVILY_API_KEY

search_tool = TavilySearchResults(max_results=5)
