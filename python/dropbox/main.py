import json

from dropbox.oauth import DropboxOAuth2FlowNoRedirect

app_key = input('Enter your app key: ')
app_secret = input('Enter your app secret: ')
flow = DropboxOAuth2FlowNoRedirect(
    consumer_key=app_key,
    consumer_secret=app_secret,
    token_access_type='offline'
)

authorize_url = flow.start()
print("\n1. Go to: {}".format(authorize_url))
print("2. Click \"Allow\" (you might have to log in first).")
print("3. Copy the authorization code.\n")

auth_code = input("Enter the authorization code here: ").strip()

try:
    oauth_result = flow.finish(auth_code)
except Exception as e:
    print("Error: {}".format(e))
    exit(1)

creds = {
    "access_token": oauth_result.access_token,
    "refresh_token": oauth_result.refresh_token,
}

out_path = "dropbox.json"
with open(out_path, "w") as f:
    json.dump(creds, f)
print("Dropbox credentials saved to {}".format(out_path))