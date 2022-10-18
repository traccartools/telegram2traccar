# About

This little Docker container gets position shared with a telegram bot, and sends location data to a [Traccar](https://www.traccar.org/) server.  

## How to

### Docker

Clone this repo and then add this to your `docker-compose.yml` file:

```yaml
  telegram2traccar:
    build: https://github.com/traccartools/telegram2traccar.git
    container_name: telegram2traccar  # optional
    environment:
      - "TELEGRAM_TOKEN" # telegram bot token
      - "TRACCAR_HOST=https://traccar.example.com" # optional, defaults to http://traccar:8082
      - "TRACCAR_OSMAND=http://traccar.example.com:5055"  # optional, defaults to http://[TRACCAR_HOST]:5055
      - "LOG_LEVEL=DEBUG"  # optional, defaults to INFO
    restart: unless-stopped
  ```
  
  * `TRACCAR_HOST` is your Traccar server's URI/URL. If run in the same docker-compose stack, name your Traccar service `traccar` and omit this env var.
  * `TRACCAR_OSMAND` is your Traccar server's Osmand protocol URL
  



### Traccar

Create a device with ID = Device ID received from bot)

