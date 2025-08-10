import json
import logging
import requests
from datetime import datetime, UTC

from dotenv import load_dotenv
from duckduckgo_search.exceptions import DuckDuckGoSearchException
from langchain.chains.base import Chain
from langchain_community.tools.ddg_search import DuckDuckGoSearchRun
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_openai import ChatOpenAI

from pydantic import BaseModel, Field
from requests import RequestException, Response

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GithubInfo(BaseModel):
  name: str = Field(description="Name of user in github repo")
  github_username: str = Field(description="Person github username")
  followers: int = Field(description="Number of followers on github")
  following: int = Field(description="Number of people following on github")
  repo_count: int = Field(description="Number of repos on github")
  description: str = Field(description="Create a small summary about the user")
  image_url: str = Field(description="Github profile pic url of the user")

#defining functions to call Github API and DuckDuckGo search

#calling github public REST api for a user and returning parsed JSON
def github_user_details(username: str) -> dict:
  response: dict = {}
  try:
    api_response = requests.get(f"https://api.github.com/users/{username}", timeout=15)
    response = api_response.json()
  except RequestException as e:
    print(f"Exception during github api call: {str(e)}")
  return response

#run DuckDuckGo search, store results to disk and return stringified version of the results
def duckduckgo_search(username: str) -> str:
  try:
    # Search for GitHub-specific information about the user
    search_query = f"GitHub {username} developer profile projects contributions"
    duckduckgo_search_tool = DuckDuckGoSearchRun()
    results = duckduckgo_search_tool.invoke({"query": search_query, "max_results": 5})
    
    # Filter results to be more relevant
    filtered_results = []
    for result in results:
      # Only include results that seem relevant to the developer
      if isinstance(result, dict):
        title = result.get('title', '')
        body = result.get('snippet', '')
      else:
        title = str(result)
        body = str(result)
      if any(keyword in title.lower() or keyword in body.lower() 
             for keyword in ['github', 'developer', 'programmer', 'coding', 'project', 'software']):
        filtered_results.append(result)
    
    # If no relevant results, try a different search
    if not filtered_results:
      alt_search_query = f"{username} software developer portfolio"
      alt_results = duckduckgo_search_tool.invoke({"query": alt_search_query, "max_results": 3})
      filtered_results = alt_results  # Take up to 3 results
    
    store_results(filtered_results, "duckduckgo_search", username)
    return str(filtered_results) if filtered_results else "No relevant developer information found"
    
  except DuckDuckGoSearchException as ex:
    logger.error(f"Error during DuckDuckGo search: {ex}")
    return "No search results available"
  except Exception as e:
    logger.error(f"Unexpected error during search: {e}")
    return "Search service unavailable"

def store_results(results: dict, result_type: str, username: str) -> None:
    store_data = {result_type: results, "username": username}
    try:
        with open("debug.json", "w") as file:
            json.dump(store_data, file, indent=4)
    except Exception as ex:
        logger.error(f"Error storing results to file: {ex}")


def create_langchain_chain():
  github_prompt = """
  User github profile data: {data}
  """

  user_prompt = """
  Using the information provided, create a comprehensive and detailed GitHub profile analysis in markdown format for the user {name} ({username}).

  Please include the following detailed sections:

  ## GitHub Profile Overview
  - Basic profile information from the user data
  - Repository count, followers, following
  - Profile description and image

  ## Recent GitHub Activity Analysis
  - **Pull Requests**: List recent PRs with titles, states, and details
  - **Commits**: Show recent commit messages and repositories
  - **Issues**: Display recent issues created or commented on
  - **Other Activities**: Any other GitHub events (releases, discussions, etc.)

  ## Activity Trends & Patterns
  - Analyze the user's contribution patterns
  - Identify most active repositories
  - Note any collaboration patterns

  ## External Context
  - Relevant information found through web search
  - Professional context and background

  ## Summary & Insights
  - Overall assessment of the user's GitHub presence
  - Strengths and areas for potential growth
  - Recommendations for profile enhancement

  User github info: {user_info}
  DuckDuckGo Search Results: {duckduckgo_results}
  GitHub Activity Data: {activity_data}
  """

  github_prompt_template = PromptTemplate.from_template(github_prompt)
  user_prompt_template = PromptTemplate.from_template(user_prompt)

  #create instance of the LLM
  llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
  llm_structured = llm.with_structured_output(GithubInfo)

  chain = (
     github_prompt_template 
     | llm_structured
        | {
            "user_info": RunnablePassthrough() | str,
            "name": RunnableLambda(lambda input: input.name),
            "username": RunnableLambda(lambda input: input.github_username),
            "duckduckgo_results": RunnableLambda(lambda input: duckduckgo_search(input.github_username)),
            "activity_data": RunnableLambda(lambda input: github_user_activity(input.github_username)),
        }
        | user_prompt_template
        | llm
        | StrOutputParser()
    )
  
  return chain

def github_user_activity(username: str) -> dict:
   #fetch recent commits, PRs, issues and calculate activity trends, return structured activity data
  """
    Fetches recent public GitHub activity for a given username.
    
    Args:
        username (str): GitHub username to fetch activity for.
        
    Returns:
        dict: Contains metadata and list of recent events (max 30 by default).
    """
  
  api_url = f"https://api.github.com/users/{username}/events/public"
  activity_data = {
     "username": username,
     "events": [],
     "fetched_at": datetime.now(UTC).isoformat()
  }
  print(f"Fetching activity for {username}")

  try:
     response = requests.get(api_url, timeout=15)
     response.raise_for_status()
     events = response.json()

     for event in events:
        parsed_event = {
           "type": event.get("type"),
           "repo": event.get("repo", {}).get("name"),
           "created_at": event.get("created_at"),
           "payload": event.get("payload", {}),
           "details": {
              "actor": event.get("actor", {}).get("login"),
              "action": event.get("payload", {}).get("action"),
              "target": event.get("payload", {}).get("target", {}).get("title"),
              "url": event.get("payload", {}).get("target", {}).get("html_url"),
           }
        }

        if event["type"] == "PushEvent":
           parsed_event["details"]["commit_messages"] = [
              commit["message"] for commit in event["payload"].get('commits', [])
           ]
        elif event["type"] == "PullRequestEvent":
          pr = event["payload"].get("pull_request", {})
          parsed_event["details"]["title"] = pr.get("title")
          parsed_event["details"]["state"] = pr.get("state")
        elif event["type"] == "IssuesEvent":
          issue = event["payload"].get("issue", {})
          parsed_event["details"]["title"] = issue.get("title")
          parsed_event["details"]["state"] = issue.get("state")

        activity_data["events"].append(parsed_event)
     return activity_data
  except Exception as e:
     logger.error(f"Error fetching GitHub activity: {str(e)}")
     return None
