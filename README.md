# AetherOnePySocial Plugin

AetherOnePySocial is a plugin for the AetherOnePy platform, providing social and analysis key management features via REST API endpoints.

## Features
- Manage analysis keys (create, read, update, delete)
- Share analysis data
- Utility endpoints for debugging and cleanup
- All endpoints are namespaced under `/aetheronepysocial` (or your configured prefix)

## Installation
1. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```
   (Run this command inside the `py/plugins/AetherOnePySocial` directory or from your project root.)
   or
   ```
   pip install -r py/plugins/AetherOnePySocial/requirements.txt
   ```
   Still sometimes it will not work, so I implemented in to setup.py of main program.

   run:
   ```
    py py/setup.py
   ```

   Im working in venv, so sometimes it shows that some modules are not installed, so run from your venv
   ```
   watchmedo auto-restart --pattern="*.py" --recursive -- C:\Users\dakan\Documents\GitHub\ae\AetherOnePy\py\.venv\Scripts\python.exe main.py --port 7000
   ```

2. **Ensure the main database exists:**
   - The plugin expects the main database at `data/aetherone.db` in your project root.
   - The database and tables are created automatically on first run if the `data` directory exists and is writable.

## Usage
- The plugin is auto-loaded by the main AetherOnePy app if placed in the `py/plugins` directory.
- Endpoints are available at:
  - `/aetheronepysocial/ping` — Health check
  - `/aetheronepysocial/local/login` — Login with email and password that you used at server (have a look at .env file for API_BASE_URL=http://localhost:8000) side usually somewhere public, you try to login via url and then you will get barrer token and then this software adds token, email, username, server_user_id (user_id on the servers side), created_at
  - `/aetheronepysocial/local/register` — Register (should be at that url, but it is possible to do it here too) with email, username and password. For server search for your url (have a look at .env file for API_BASE_URL=http://localhost:8000) side usually somewhere public, you try to login via url and then you will get barrer token and then this software adds token, email, username, server_user_id (user_id on the servers side), created_at
  - `/register`, `/login` - for local db there is only one user that is needed in users database check -> database.py upsert_user_token
  
  - `/aetheronepysocial/key` POST - create a new key create_analysis_key() 
  it is important to call this 
  `{
    "local_session_id": 1
  }`
  but user has to be logged in, so you need to login, so token will be saved in local social.db users and there should be only one user! this will save copy of what is on server to local. 
  - `/aetheronepysocial/key/<int:user_id>` GET - you will get all from that user_id from local database social.db and from server get keys/
  ```
        {
        "data": {
            "local": [
                {
                    "created_at": "2025-06-11 12:54:21",
                    "expires_at": null,
                    "id": 1,
                    "key": "9e3ffbd7-e652-4d2f-a262-aeea665001e1",
                    "key_id": 2,
                    "metadata": "{\"created_from\": \"key_endpoint\", \"timestamp\": \"2025-06-11T14:54:21.310535\"}",
                    "session_id": 1,
                    "status": "active",
                    "user_id": 4
                }
            ],
            "server": [
                {
                    "created": "2025-06-11T12:14:07.114104+00:00",
                    "id": 2,
                    "key": "9e3ffbd7-e652-4d2f-a262-aeea665001e1",
                    "local_session_id": 1,
                    "session_id": null,
                    "used": false,
                    "used_at": null,
                    "user_id": 4
                }
            ],
            "user_id": 4
        },
        "message": "Found 1 keys for user_id server side use_id  4",
        "status": "success"
    }
  ```
  - `/aetheronepysocial/key/<string:key>` GET - def get_analysis_key(key) same as above you will get from server and local, but you need to login
  - `/aetheronepysocial/key/9e3ffbd7-e652-4d2f-a262-aeea665001e1` PUT - will update used and time on server and local in analysis_key status used
  ```
  {
    "used": true,
    "status": "used"
  }
  ```
  TODO: 
  - `/delete key` - delete key needs to be done /key/<string:key>', methods=['DELETE'] is not yet implemented to server and question is if that is needed

  same for /keys/cleanup


  - `/aetheronepysocial/analysis` — Share analysis data nees to be tested!!!
  - `/aetheronepysocial/debug_routes` — List plugin routes

## Development & Debugging
- To see only the plugin's routes, visit `/aetheronepysocial/debug_routes`.
- For hot-reload during development, use Flask's debug mode or an external watcher like `watchdog`:
  ```sh
  watchmedo auto-restart --pattern="*.py" --recursive -- python main.py --port 7000
  ```
- Debug print statements are included in the plugin for blueprint creation and route access.

## Notes
- If you change the URL prefix in the main app, update the `prefix` variable in `debug_routes` accordingly.
- Requires the main AetherOnePy app to be running.

## License
MIT 