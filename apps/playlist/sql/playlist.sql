ALTER TABLE "auth_user" ALTER "first_name" TYPE varchar(130);
select setval('music_artist_id_seq'::regclass, 30000);
select setval('music_track_id_seq'::regclass, 30000);
select setval('playlist_playlist_id_seq'::regclass, 30000);
select setval('auth_user_id_seq'::regclass, 30000);
