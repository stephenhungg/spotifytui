"""
VibeChain API client for ML-powered music recommendations
"""

import requests
import logging
from typing import Dict, List, Optional, Any
import asyncio
import aiohttp
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class TrackFeatures:
    """Spotify track features for ML analysis"""
    danceability: float
    energy: float
    valence: float
    tempo: float
    acousticness: float = 0.0
    instrumentalness: float = 0.0
    liveness: float = 0.0
    speechiness: float = 0.0

@dataclass
class VibePrediction:
    """AI prediction for next track vibe"""
    danceability: float
    energy: float
    valence: float
    tempo: float
    confidence: float = 0.0

class VibeChainClient:
    """Client for VibeChain ML recommendation API"""
    
    def __init__(self, api_url: str = "http://localhost:8080"):
        self.api_url = api_url.rstrip('/')
        self.session = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def health_check(self) -> bool:
        """Check if VibeChain API is healthy"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            url = f"{self.api_url}/health"
            
            async with self.session.get(url, timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("status") == "healthy"
                return False
        except Exception as e:
            logger.warning(f"VibeChain health check failed: {e}")
            return False
    
    async def predict_next_vibe(self, current_tracks: List[TrackFeatures]) -> Optional[VibePrediction]:
        """
        Predict what the next track's vibe should be based on current listening session
        
        Args:
            current_tracks: List of recent track features (max 5 for best results)
            
        Returns:
            VibePrediction object with predicted features, or None if failed
        """
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            # Convert TrackFeatures to VibeChain API format
            tracks_data = []
            for track in current_tracks[-1:]:  # Use only the last track for now
                # Convert Spotify features to VibeChain format with all required fields
                track_data = {
                    "danceability": track.danceability,
                    "energy": track.energy,
                    "valence": track.valence,
                    "speechiness": track.speechiness,
                    "acousticness": track.acousticness,
                    "instrumentalness": track.instrumentalness,
                    "liveness": track.liveness,
                    "key": 0.5,  # Default normalized key
                    "loudness": 0.5,  # Default normalized loudness
                    "mode": 1.0,  # Default to major
                    "tempo": min(track.tempo / 200.0, 1.0),  # Normalize tempo to 0-1
                    "duration_ms": 0.5,  # Default normalized duration
                    "time_signature": 0.8,  # Default 4/4 time signature
                    # Context features
                    "hour_of_day": (datetime.now().hour) / 24.0,
                    "day_of_week": (datetime.now().weekday()) / 7.0,
                    "month": (datetime.now().month - 1) / 12.0,
                    "is_weekend": 1.0 if datetime.now().weekday() >= 5 else 0.0,
                    # Default user behavior
                    "skip_rate": 0.1,
                    "repeat_count": 0.1,
                    "playlist_position": 0.5
                }
                tracks_data.append(track_data)
            
            payload = {
                "tracks": tracks_data,
                "options": {
                    "include_insights": False
                }
            }
            url = f"{self.api_url}/analyze"

            async with self.session.post(
                url,
                json=payload,
                timeout=10,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status != 200:
                    logger.error(f"VibeChain API error: {response.status}")
                    return None
                    
                data = await response.json()
                
                # Parse prediction from new API response format
                if data.get("success") and "data" in data:
                    predictions = data["data"]["predictions"]
                    mood_pred = predictions.get("mood_prediction", {})
                    confidence = predictions.get("confidence_scores", {})
                    
                    return VibePrediction(
                        danceability=mood_pred.get("arousal", 0.5),  # arousal maps to danceability
                        energy=mood_pred.get("energy", 0.5),
                        valence=mood_pred.get("valence", 0.5),
                        tempo=120.0,  # Default tempo
                        confidence=confidence.get("mood", 0.0)
                    )
                
                return None
                
        except Exception as e:
            logger.error(f"Failed to get vibe prediction: {e}")
            return None
    
    def predict_next_vibe_sync(self, current_tracks: List[TrackFeatures]) -> Optional[VibePrediction]:
        """Synchronous wrapper for predict_next_vibe"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        return loop.run_until_complete(self._predict_sync_helper(current_tracks))
    
    async def _predict_sync_helper(self, current_tracks: List[TrackFeatures]) -> Optional[VibePrediction]:
        """Helper for sync prediction"""
        async with self as client:
            return await client.predict_next_vibe(current_tracks)

    def extract_track_features(self, spotify_track: Dict[str, Any]) -> TrackFeatures:
        """
        Extract features from Spotify track object (with audio features)
        
        Args:
            spotify_track: Spotify track dict that includes audio_features
            
        Returns:
            TrackFeatures object
        """
        features = spotify_track.get("audio_features", {})
        
        return TrackFeatures(
            danceability=features.get("danceability", 0.5),
            energy=features.get("energy", 0.5),
            valence=features.get("valence", 0.5),
            tempo=features.get("tempo", 120.0),
            acousticness=features.get("acousticness", 0.0),
            instrumentalness=features.get("instrumentalness", 0.0),
            liveness=features.get("liveness", 0.0),
            speechiness=features.get("speechiness", 0.0)
        )
    
    def find_matching_tracks(self, prediction: VibePrediction, available_tracks: List[Dict]) -> List[Dict]:
        """
        Find tracks from user's library that match the AI prediction
        
        Args:
            prediction: VibePrediction from the ML model
            available_tracks: List of user's tracks with audio features
            
        Returns:
            List of tracks sorted by how well they match the prediction
        """
        matches = []
        
        for track in available_tracks:
            features = track.get("audio_features", {})
            if not features:
                continue
                
            # Calculate similarity score (lower = better match)
            score = 0
            score += abs(features.get("danceability", 0.5) - prediction.danceability) * 2
            score += abs(features.get("energy", 0.5) - prediction.energy) * 2
            score += abs(features.get("valence", 0.5) - prediction.valence) * 2
            score += abs((features.get("tempo", 120) / 200) - (prediction.tempo / 200)) * 1
            
            matches.append((track, score))
        
        # Sort by best match (lowest score)
        matches.sort(key=lambda x: x[1])
        
        return [track for track, score in matches[:10]]  # Return top 10 matches
