-- Stored Procedure: sinkronisasi_rekam_medis_jadwal
CREATE OR REPLACE FUNCTION sinkronisasi_rekam_medis_jadwal()
RETURNS TRIGGER AS $$
DECLARE
    tgl_rekam DATE;
    v_id_hewan UUID;
    nama_hewan TEXT;
    tgl_jadwal DATE;
    freq INTEGER;
BEGIN
    -- Ambil id_hewan (UUID) dan tanggal rekam medis yang baru dimasukkan
    v_id_hewan := NEW.id_hewan;
    tgl_rekam := NEW.tanggal_pemeriksaan;

    -- Jika status kesehatan Sakit, lakukan sinkronisasi jadwal
    IF NEW.status_kesehatan = 'Sakit' THEN
        -- Cari jadwal pemeriksaan terdekat setelah tanggal rekam medis
        SELECT tgl_pemeriksaan_selanjutnya, freq_pemeriksaan_rutin INTO tgl_jadwal, freq
        FROM jadwal_pemeriksaan_kesehatan
        WHERE id_hewan = v_id_hewan AND tgl_pemeriksaan_selanjutnya >= tgl_rekam
        ORDER BY tgl_pemeriksaan_selanjutnya ASC
        LIMIT 1;

        IF tgl_jadwal IS NOT NULL THEN
            -- Update jadwal terdekat menjadi 7 hari setelah rekam medis
            UPDATE jadwal_pemeriksaan_kesehatan
            SET tgl_pemeriksaan_selanjutnya = tgl_rekam + INTERVAL '7 days'
            WHERE id_hewan = v_id_hewan AND tgl_pemeriksaan_selanjutnya = tgl_jadwal;
        ELSE
            -- Jika tidak ada jadwal, buat jadwal baru 7 hari setelah rekam medis
            -- Default freq 3 jika tidak ada data
            IF freq IS NULL THEN freq := 3; END IF;
            INSERT INTO jadwal_pemeriksaan_kesehatan (id_hewan, tgl_pemeriksaan_selanjutnya, freq_pemeriksaan_rutin)
            VALUES (v_id_hewan, tgl_rekam + INTERVAL '7 days', freq);
        END IF;

        -- Ambil nama hewan untuk pesan
        SELECT nama INTO nama_hewan FROM hewan WHERE id = v_id_hewan;
        RAISE NOTICE 'SUKSES: Jadwal pemeriksaan hewan "%" telah diperbarui karena status kesehatan "Sakit".', nama_hewan;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger: after insert on catatan_medis
DROP TRIGGER IF EXISTS after_insert_catatan_medis ON catatan_medis;
CREATE TRIGGER after_insert_catatan_medis
AFTER INSERT ON catatan_medis
FOR EACH ROW EXECUTE FUNCTION sinkronisasi_rekam_medis_jadwal();
