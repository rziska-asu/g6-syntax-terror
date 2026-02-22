-- Run this after MUSIC_SCHEMA.sql if you already have the DB. Adds disliked_tracks and skipped_tracks.
USE music_discovery_engine;

CREATE TABLE IF NOT EXISTS disliked_tracks (
	id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
	user_id BIGINT UNSIGNED NOT NULL,
	artist_name VARCHAR(255) NOT NULL,
	track_name VARCHAR(255) NOT NULL,
	lastfm_url VARCHAR(500) NULL,
	created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
	PRIMARY KEY (id),
	UNIQUE KEY disliked_user_tracks (user_id, artist_name, track_name),
	KEY idx_disliked_user_created (user_id, created_at),
	CONSTRAINT fk_disliked_tracks
		FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS skipped_tracks (
	id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
	user_id BIGINT UNSIGNED NOT NULL,
	artist_name VARCHAR(255) NOT NULL,
	track_name VARCHAR(255) NOT NULL,
	lastfm_url VARCHAR(500) NULL,
	created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
	PRIMARY KEY (id),
	UNIQUE KEY skipped_user_tracks (user_id, artist_name, track_name),
	KEY idx_skipped_user_created (user_id, created_at),
	CONSTRAINT fk_skipped_tracks
		FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;
