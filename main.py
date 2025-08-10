from langchain_pipeline import github_user_details, github_user_activity, create_langchain_chain, logger

if __name__ == "__main__":
  # Take the username that you want to use to create the markdown text
  username = "derrikzzz"
  
  # Fetch both user data and activity
  github_user_data = github_user_details(username=username)
  activity_data = github_user_activity(username=username)
  
  print(f"GitHub User Data: {github_user_data}")
  print(f"Activity Data: {activity_data}")

  # Create the langchain chain
  chain = create_langchain_chain()

  # Invoke the langchain chain
  output = chain.invoke({"data": str(github_user_data)})

  # Print the output
  logger.info(f"Output for {username}: {output}")

