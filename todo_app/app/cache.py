import os
import time
import json
import logging
import aiohttp

namespace = os.getenv("POD_NAMESPACE", "default")
logger = logging.getLogger(f"{namespace}-todo-frontend")

class ImageCache:
  def __init__(self, cache_dir: str = "./cache", ttl: int = 600):
      self.cache_dir = cache_dir
      self.ttl = ttl
      self.image_path = os.path.join(cache_dir, "cached_image.jpg")
      self.metadata_path = os.path.join(cache_dir, "cache_metadata.json")
      self.grace_period_used = False
      self.access_count = 0 # total access count
      self.image_access_count = 0 # per image access count
      self.last_access_time = None
      self.download_timestamp = None  # Timestamp of image fetch
      os.makedirs(cache_dir, exist_ok=True)
      self._load_metadata()
      logger.info(f"ImageCache initialized with cache_dir: {cache_dir}, ttl: {ttl}s")

  def _load_metadata(self):
      if os.path.exists(self.metadata_path):
          logger.info(f"Loading metadata from {self.metadata_path}")
          try:
              with open(self.metadata_path, "r") as f:
                  data = json.load(f)
              self.grace_period_used = data.get("grace_period_used", False)
              self.access_count = data.get("access_count", 0)
              self.last_access_time = data.get("last_access_time", None)
              self.download_timestamp = data.get("download_timestamp", None)
              self.image_access_count = data.get("image_access_count", 0)
              logger.info(f"Loaded metadata: {data}")

          except Exception as e:
              logger.error(f"Failed to load cache metadata: {e}")
              self._reset_metadata()
      else:
          logger.info(f"No metadata file found at {self.metadata_path}, initializing defaults")
          self._reset_metadata()

  def _reset_metadata(self):
      self.grace_period_used = False
      self.access_count = 0
      self.last_access_time = None
      self.download_timestamp = None
      self.image_access_count = 0
      self._save_metadata()

  def _save_metadata(self):
      data = {
          "grace_period_used": self.grace_period_used,
          "access_count": self.access_count,
          "last_access_time": self.last_access_time,
          "download_timestamp": self.download_timestamp,
          "image_access_count": self.image_access_count,
      }
      try:
          with open(self.metadata_path, "w") as f:
              json.dump(data, f)
      except Exception as e:
          print(f"Failed to save cache metadata: {e}")

  def record_access(self):
      self.access_count += 1
      self.image_access_count += 1
      self.last_access_time = time.time()
      self._save_metadata()

  
  def is_cache_expired(self) -> bool:
      """Check if cache is expired or missing."""
      if not os.path.exists(self.image_path) or self.download_timestamp is None:
        logger.info("Cache expired: Missing image or download timestamp")
        return True
      
      age = time.time() - self.download_timestamp
      logger.info(f"Cache age: {age}s, TTL: {self.ttl}s, Expired: {age > self.ttl}")
      return age > self.ttl

  async def fetch_and_cache_image(self) -> bool:
      """Fetch a random image and cache it locally."""
      logger.info("Fetching new image from external source")
      img_url = os.getenv("IMG_URL", "https://picsum.photos/500")
      logger.info(f"cache,py img_url: {img_url}")      
      #img_url = "https://picsum.photos/500"
      try:
          async with aiohttp.ClientSession() as session:
              async with session.get(img_url) as resp:
                  if resp.status == 200:
                      img_bytes = await resp.read()
                      with open(self.image_path, "wb") as f:
                          f.write(img_bytes)
                      self.download_timestamp = time.time()
                      # Reset grace period flag on new fetch
                      self.grace_period_used = False
                      self._save_metadata()
                      logger.info(f"Image fetched and cached successfully at {self.download_timestamp}")
                      return True
      except Exception as e:
          logger.error(f"Failed to fetch image: {e}")
      return False

