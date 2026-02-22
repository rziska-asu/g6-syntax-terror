-- create music_discovery_engine database
CREATE DATABASE IF NOT EXISTS music_discovery_engine
	DEFAULT CHARACTER SET utf8mb4
	DEFAULT COLLATE utf8mb4_0900_ai_ci;

USE music_discovery_engine;

-- create user tables
CREATE TABLE IF NOT EXISTS users(
	id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL default NULL,
    PRIMARY KEY (id),
    UNIQUE KEY users_username (username),
    UNIQUE KEY users_email(email)
    
)ENGINE=InnoDB;
-- Create user_sessions table
CREATE TABLE IF NOT EXISTS user_sessions(
	user_id BIGINT UNSIGNED NOT NULL,
    latest_quiz JSON NULL,
    latest_results JSON NULL,
    
    updated_at TIMESTAMP NOT NULL
		DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,
        
        PRIMARY KEY(user_id),
        
        CONSTRAINT fk_user_sessions
			FOREIGN KEY (user_id) REFERENCES users(id)
			ON DELETE CASCADE 
    
    
)Engine=InnoDB;

-- Create likes/saves table
CREATE TABLE IF NOT EXISTS liked_tracks (
	id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id BIGINT UNSIGNED NOT NULL,
    artist_name varchar(255) NOT NULL,
    track_name VARCHAR(255) NOT NULL,
    lastfm_url VARCHAR(500) NULL,
    itunes_url VARCHAR(500) NULL,
    album_name VARCHAR(255) NULL,
    image_url VARCHAR(500) NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY(id),
    -- user cannot like the same track twice
    UNIQUE KEY liked_user_tracks(user_id, artist_name, track_name),
    
    KEY id_liked_user_created (user_id, created_at),
    CONSTRAINT fk_liked_tracks
		FOREIGN KEY(user_id) REFERENCES users(id)
		ON DELETE CASCADE
)ENGINE=InnoDB;

-- Disliked tracks (for learning; influences recommendations)
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

-- Skipped tracks (for learning; influences recommendations)
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

-- Create history table
CREATE TABLE IF NOT EXISTS history_runs(
	id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id BIGINT UNSIGNED NOT NULL,
    
	quiz_input JSON NOT NULL,
    results_output JSON NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY(id),
    
    KEY id_history_runs_created(user_id, created_at),
    
    CONSTRAINT fk_history_run
		foreign key(user_id) REFERENCES users(id)
        ON DELETE CASCADE
)ENGINE=InnoDB;





