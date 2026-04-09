"""
Audio feature estimation when Spotify's audio_features API is unavailable
"""

import re
from typing import Dict, Optional
from datetime import datetime
from vibechain_client import TrackFeatures

class AudioFeatureEstimator:
    """Estimate audio features from available track metadata"""
    
    def __init__(self):
        # Genre-based feature mappings
        self.genre_features = {
            # Electronic/Dance
            'edm': {'danceability': 0.8, 'energy': 0.9, 'valence': 0.7, 'acousticness': 0.1},
            'house': {'danceability': 0.9, 'energy': 0.8, 'valence': 0.6, 'acousticness': 0.1},
            'techno': {'danceability': 0.8, 'energy': 0.9, 'valence': 0.5, 'acousticness': 0.1},
            'dubstep': {'danceability': 0.7, 'energy': 0.9, 'valence': 0.6, 'acousticness': 0.1},
            
            # Hip-Hop/Rap
            'hip hop': {'danceability': 0.7, 'energy': 0.7, 'valence': 0.6, 'speechiness': 0.3},
            'rap': {'danceability': 0.7, 'energy': 0.7, 'valence': 0.6, 'speechiness': 0.4},
            'trap': {'danceability': 0.8, 'energy': 0.8, 'valence': 0.5, 'speechiness': 0.2},
            
            # Rock
            'rock': {'danceability': 0.5, 'energy': 0.8, 'valence': 0.6, 'acousticness': 0.2},
            'metal': {'danceability': 0.4, 'energy': 0.9, 'valence': 0.4, 'acousticness': 0.1},
            'punk': {'danceability': 0.6, 'energy': 0.9, 'valence': 0.5, 'acousticness': 0.2},
            
            # Pop
            'pop': {'danceability': 0.7, 'energy': 0.7, 'valence': 0.7, 'acousticness': 0.3},
            'indie pop': {'danceability': 0.6, 'energy': 0.6, 'valence': 0.6, 'acousticness': 0.4},
            
            # Folk/Acoustic
            'folk': {'danceability': 0.4, 'energy': 0.4, 'valence': 0.5, 'acousticness': 0.8},
            'acoustic': {'danceability': 0.3, 'energy': 0.3, 'valence': 0.5, 'acousticness': 0.9},
            'country': {'danceability': 0.5, 'energy': 0.5, 'valence': 0.6, 'acousticness': 0.6},
            
            # Jazz/Blues
            'jazz': {'danceability': 0.5, 'energy': 0.4, 'valence': 0.5, 'acousticness': 0.7, 'instrumentalness': 0.6},
            'blues': {'danceability': 0.4, 'energy': 0.5, 'valence': 0.4, 'acousticness': 0.6},
            
            # Classical
            'classical': {'danceability': 0.2, 'energy': 0.3, 'valence': 0.5, 'acousticness': 0.9, 'instrumentalness': 0.9},
            
            # R&B/Soul
            'r&b': {'danceability': 0.7, 'energy': 0.6, 'valence': 0.6, 'acousticness': 0.3},
            'soul': {'danceability': 0.6, 'energy': 0.6, 'valence': 0.6, 'acousticness': 0.4},
            
            # Ambient/Chill
            'ambient': {'danceability': 0.2, 'energy': 0.2, 'valence': 0.5, 'acousticness': 0.5, 'instrumentalness': 0.8},
            'chill': {'danceability': 0.4, 'energy': 0.3, 'valence': 0.6, 'acousticness': 0.5},
        }
        
        # Tempo ranges by genre
        self.genre_tempo = {
            'edm': (120, 140), 'house': (120, 130), 'techno': (120, 140),
            'hip hop': (70, 100), 'rap': (80, 110), 'trap': (140, 180),
            'rock': (110, 140), 'metal': (120, 180), 'punk': (150, 200),
            'pop': (100, 130), 'folk': (80, 120), 'jazz': (60, 120),
            'classical': (60, 120), 'ambient': (60, 100)
        }
    
    def estimate_features(self, track_data: Dict) -> TrackFeatures:
        """
        Estimate audio features from track metadata
        
        Args:
            track_data: Spotify track object
            
        Returns:
            TrackFeatures with estimated values
        """
        # Get basic track info
        track_name = track_data.get('name', '').lower()
        artists = track_data.get('artists', [])
        album = track_data.get('album', {})
        duration_ms = track_data.get('duration_ms', 180000)  # Default 3 minutes
        popularity = track_data.get('popularity', 50)
        explicit = track_data.get('explicit', False)
        
        # Get artist genres
        genres = []
        for artist in artists:
            artist_genres = artist.get('genres', [])
            genres.extend([g.lower() for g in artist_genres])
        
        # Album genres (if available)
        album_genres = album.get('genres', [])
        genres.extend([g.lower() for g in album_genres])
        
        # Estimate features based on genres
        estimated_features = self._estimate_from_genres(genres)
        
        # Adjust based on track name patterns
        estimated_features = self._adjust_from_track_name(track_name, estimated_features)
        
        # Adjust based on popularity and other metadata
        estimated_features = self._adjust_from_metadata(
            estimated_features, popularity, explicit, duration_ms
        )
        
        # Convert to normalized values and create TrackFeatures
        return TrackFeatures(
            danceability=estimated_features.get('danceability', 0.5),
            energy=estimated_features.get('energy', 0.5),
            valence=estimated_features.get('valence', 0.5),
            tempo=estimated_features.get('tempo', 120.0),
            acousticness=estimated_features.get('acousticness', 0.5),
            instrumentalness=estimated_features.get('instrumentalness', 0.1),
            liveness=estimated_features.get('liveness', 0.1),
            speechiness=estimated_features.get('speechiness', 0.1)
        )
    
    def _estimate_from_genres(self, genres: list) -> Dict[str, float]:
        """Estimate features based on artist/album genres"""
        if not genres:
            return {
                'danceability': 0.5, 'energy': 0.5, 'valence': 0.5,
                'tempo': 120.0, 'acousticness': 0.5, 'instrumentalness': 0.1,
                'liveness': 0.1, 'speechiness': 0.1
            }
        
        # Find matching genres
        matched_features = []
        for genre in genres:
            for known_genre, features in self.genre_features.items():
                if known_genre in genre:
                    matched_features.append(features)
                    break
        
        if not matched_features:
            # Default pop-like features
            matched_features = [self.genre_features['pop']]
        
        # Average the matched features
        avg_features = {}
        for key in ['danceability', 'energy', 'valence', 'acousticness', 'instrumentalness', 'speechiness']:
            values = [f.get(key, 0.5) for f in matched_features]
            avg_features[key] = sum(values) / len(values)
        
        # Estimate tempo
        tempo_ranges = []
        for genre in genres:
            for known_genre, tempo_range in self.genre_tempo.items():
                if known_genre in genre:
                    tempo_ranges.append(tempo_range)
                    break
        
        if tempo_ranges:
            min_tempo = sum(r[0] for r in tempo_ranges) / len(tempo_ranges)
            max_tempo = sum(r[1] for r in tempo_ranges) / len(tempo_ranges)
            avg_features['tempo'] = (min_tempo + max_tempo) / 2
        else:
            avg_features['tempo'] = 120.0
        
        avg_features['liveness'] = 0.1  # Default low liveness
        
        return avg_features
    
    def _adjust_from_track_name(self, track_name: str, features: Dict[str, float]) -> Dict[str, float]:
        """Adjust features based on track name patterns"""
        # Live versions
        if any(word in track_name for word in ['live', 'concert', 'tour']):
            features['liveness'] = min(0.9, features['liveness'] + 0.4)
            features['energy'] = min(1.0, features['energy'] + 0.1)
        
        # Acoustic versions
        if any(word in track_name for word in ['acoustic', 'unplugged', 'stripped']):
            features['acousticness'] = min(1.0, features['acousticness'] + 0.3)
            features['energy'] = max(0.1, features['energy'] - 0.2)
            features['danceability'] = max(0.1, features['danceability'] - 0.2)
        
        # Remix versions
        if any(word in track_name for word in ['remix', 'mix', 'edit']):
            features['danceability'] = min(1.0, features['danceability'] + 0.2)
            features['energy'] = min(1.0, features['energy'] + 0.1)
        
        # Instrumental versions
        if any(word in track_name for word in ['instrumental', 'karaoke']):
            features['instrumentalness'] = min(1.0, features['instrumentalness'] + 0.5)
            features['speechiness'] = max(0.0, features['speechiness'] - 0.3)
        
        # Sad/emotional indicators
        if any(word in track_name for word in ['sad', 'cry', 'tears', 'lonely', 'blue']):
            features['valence'] = max(0.1, features['valence'] - 0.3)
            features['energy'] = max(0.1, features['energy'] - 0.1)
        
        # Happy/upbeat indicators
        if any(word in track_name for word in ['happy', 'party', 'dance', 'celebration']):
            features['valence'] = min(1.0, features['valence'] + 0.3)
            features['danceability'] = min(1.0, features['danceability'] + 0.2)
            features['energy'] = min(1.0, features['energy'] + 0.1)
        
        return features
    
    def _adjust_from_metadata(self, features: Dict[str, float], popularity: int, 
                            explicit: bool, duration_ms: int) -> Dict[str, float]:
        """Adjust features based on track metadata"""
        # Popularity adjustments (popular songs tend to be more danceable/energetic)
        if popularity > 70:
            features['danceability'] = min(1.0, features['danceability'] + 0.1)
            features['energy'] = min(1.0, features['energy'] + 0.05)
        elif popularity < 30:
            # Less popular might be more experimental/less mainstream
            features['acousticness'] = min(1.0, features['acousticness'] + 0.1)
        
        # Explicit content might indicate more aggressive/energetic music
        if explicit:
            features['energy'] = min(1.0, features['energy'] + 0.05)
            features['speechiness'] = min(1.0, features['speechiness'] + 0.1)
        
        # Duration adjustments
        duration_minutes = duration_ms / 60000
        if duration_minutes > 6:  # Long tracks might be more instrumental/ambient
            features['instrumentalness'] = min(1.0, features['instrumentalness'] + 0.1)
        elif duration_minutes < 2.5:  # Short tracks might be more energetic
            features['energy'] = min(1.0, features['energy'] + 0.05)
        
        return features

    def get_fallback_features(self) -> TrackFeatures:
        """Get generic fallback features when no data is available"""
        return TrackFeatures(
            danceability=0.5,
            energy=0.5,
            valence=0.5,
            tempo=120.0,
            acousticness=0.5,
            instrumentalness=0.1,
            liveness=0.1,
            speechiness=0.1
        )
