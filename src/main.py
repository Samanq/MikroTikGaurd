from routeros_api import RouterOsApiPool
import sys

# MikroTik connection details
HOST = '192.168.1.88'   # Replace with your MikroTik IP
USERNAME = 'admin'      # Replace with your username
PASSWORD = 'admin'      # Replace with your password
PORT = 8728             # Default API port (change if customized)

def connect_to_router():
    print(f"Attempting to connect to {HOST}:{PORT} with username '{USERNAME}'...")
    
    try:
        # Create API connection pool
        api_pool = RouterOsApiPool(HOST, username=USERNAME, password=PASSWORD, 
                                  port=PORT, use_ssl=False, plaintext_login=True)
        api = api_pool.get_api()
        print("Connection successful!")
        return api_pool, api
    except Exception as e:
        print(f"Authentication error: {e}")
        print("\nPossible solutions:")
        print("1. Verify username and password")
        print("2. Check if the router allows API access")
        print("3. Verify if the router's API service is enabled")
        print("4. Check if your IP is allowed to connect to the router")
        sys.exit(1)

try:
    api_pool, api = connect_to_router()

    # Get only backup files and sort by name
    file_resource = api.get_resource('/file')
    
    # Filter for backup files only
    backup_files = file_resource.get(type='backup')
    
    # Check if "safe-backup" exists
    safe_backup_exists = any(file['name'] == 'safe-backup.backup' for file in backup_files)
    
    if safe_backup_exists:
        print("\nsafe backup found")
        
        try:
            import time
            
            # Wait for 1 minute with countdown
            total_seconds = 60
            for remaining in range(total_seconds, 0, -1):
                sys.stdout.write(f"\rBackup will be restored in {remaining} seconds")
                sys.stdout.flush()
                time.sleep(1)
            print("\nTime's up! Proceeding with backup restoration...")
            
            system_backup_resource = api.get_resource('/system/backup')

            print("Attempting to restore safe-backup.backup...")
            system_backup_resource.call('load', {
                'name': 'safe-backup.backup',
                'password': '' # Empty string for no password, or provide the backup password if it has one
            })
            print("Backup restoration initiated. The router will reboot automatically.")
            
        except Exception as e:
            print(f"Error restoring backup: {e}")
            print("Attempting to reconnect and retry restoration...")
            
            try:
                # Close the existing connection
                api_pool.disconnect()
                
                # Reconnect to the router
                api_pool, api = connect_to_router()
                
                # Try restoring backup again
                system_backup_resource = api.get_resource('/system/backup')
                print("Retrying backup restoration...")
                system_backup_resource.call('load', {
                    'name': 'safe-backup.backup',
                    'password': '' # Empty string for no password
                })
                print("Backup restoration retry initiated. The router will reboot automatically.")
                
            except Exception as retry_error:
                print(f"Retry failed: {retry_error}")
                print("Could not restore backup after retry. Manual intervention may be required.")
    else:
        print("\nsafebackup does not exist")

    # Close API connection
    api_pool.disconnect()

except Exception as e:
    print(f"Error during operation: {e}")
