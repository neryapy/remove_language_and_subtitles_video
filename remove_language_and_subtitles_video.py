import os
import subprocess
import ffmpeg
import sys
from tqdm import tqdm  # For progress bars

def list_streams(input_video_path):
    try:
        # Probe the video to find audio and subtitle streams
        probe = ffmpeg.probe(input_video_path)
        streams = probe['streams']

        # Print all audio and subtitle tracks with their language codes
        print(f"Streams in {input_video_path}:")
        for stream in streams:
            if stream['codec_type'] in ['audio', 'subtitle']:
                stream_type = stream['codec_type']
                language = stream.get('tags', {}).get('language', 'unknown')
                print(f"Stream index: {stream['index']}, Type: {stream_type}, Language: {language}")
    except ffmpeg.Error as e:
        print(f"Error processing {input_video_path}: {e.stderr.decode()}", file=sys.stderr)


def list_audio_tracks(input_video_path):
    try:
        # Probe the video to find the audio tracks
        probe = ffmpeg.probe(input_video_path)
        audio_streams = [stream for stream in probe['streams'] if stream['codec_type'] == 'audio']

        # Print all audio tracks with their language codes
        print(f"Audio tracks in {input_video_path}:")
        for stream in audio_streams:
            language = stream.get('tags', {}).get('language', 'unknown')
            print(f"Stream index: {stream['index']}, Language: {language}")
    except ffmpeg.Error as e:
        print(f"Error processing {input_video_path}: {e.stderr.decode()}", file=sys.stderr)


def remove_audio_track(input_video_path, output_video_path, language_code):
    try:
        # Probe the video to find the audio tracks
        probe = ffmpeg.probe(input_video_path)
        audio_streams = [stream for stream in probe['streams'] if stream['codec_type'] == 'audio']

        # Find the audio track with the specified language code
        audio_track_to_remove = None
        for stream in audio_streams:
            if 'tags' in stream and stream['tags'].get('language') == language_code:
                audio_track_to_remove = stream['index']
                break

        if audio_track_to_remove is None:
            print(f"No audio track with language code {language_code} found in {input_video_path}")
            return

        # Prepare filter to remove the specified audio track
        map_str = ''.join([f'-map 0:{i} ' for i in range(len(probe['streams'])) if i != audio_track_to_remove])

        # Build the ffmpeg command with re-encoding options
        ffmpeg_cmd = [
            'ffmpeg', '-i', input_video_path] + map_str.split() + [
            '-c:v', 'copy', '-c:a', 'copy', output_video_path
        ]

        # Execute the ffmpeg command with input redirected to always say "y" for overwrite
        p = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        p.communicate(input=b'y\n')  # Automatically answers "y" to the overwrite prompt

    except ffmpeg.Error as e:
        print(f"Error processing {input_video_path}: {e.stderr.decode()}", file=sys.stderr)


def remove_subtitle_tracks(input_video_path, output_video_path):
    try:
        # Probe the video to find subtitle tracks
        probe = ffmpeg.probe(input_video_path)
        subtitle_streams = [stream['index'] for stream in probe['streams'] if stream['codec_type'] == 'subtitle']

        if not subtitle_streams:
            print(f"No subtitle tracks found in {input_video_path}")
            return

        # Prepare filter to remove all subtitle tracks
        map_str = ''.join([f'-map 0:{i} ' for i in range(len(probe['streams'])) if i not in subtitle_streams])

        # Build the ffmpeg command with re-encoding options
        ffmpeg_cmd = [
            'ffmpeg', '-i', input_video_path] + map_str.split() + [
            '-c:v', 'copy', '-c:a', 'copy', output_video_path
        ]

        # Execute the ffmpeg command with input redirected to always say "y" for overwrite
        p = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        p.communicate(input=b'y\n')  # Automatically answers "y" to the overwrite prompt

    except ffmpeg.Error as e:
        print(f"Error processing {input_video_path}: {e.stderr.decode()}", file=sys.stderr)


def process_videos_in_folder(input_folder, output_folder, language_code, with_sub):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for root, dirs, files in os.walk(input_folder):
        video_files = [file for file in files if file.endswith(('.mp4', '.mkv', '.avi', '.mov'))]
        if not video_files:
            continue

        # Get the parent folder name where the video file is located
        parent_folder_name = os.path.basename(root)
        output_subfolder = os.path.join(output_folder, parent_folder_name)

        if not os.path.exists(output_subfolder):
            os.makedirs(output_subfolder)

        # Initialize tqdm progress bar
        with tqdm(total=len(video_files), desc=f"Processing videos in {root}") as pbar:
            for file in video_files:
                input_video_path = os.path.join(root, file)
                output_video_path = os.path.join(output_subfolder, file)

                try:
                    list_audio_tracks(input_video_path)

                    # Create a temporary file path for processing with subtitles removed
                    temp_output_path = os.path.join(output_folder, f"temp_{file}")

                    # Remove audio tracks with specified language code
                    remove_audio_track(input_video_path, temp_output_path, language_code)

                    # Remove subtitles if requested
                    if with_sub.lower() == 'y':
                        remove_subtitle_tracks(temp_output_path, output_video_path)
                    else:
                        # If subtitles are not removed, rename the temp file to the output file
                        os.rename(temp_output_path, output_video_path)

                    # Delete the temporary file if it exists
                    if os.path.exists(temp_output_path):
                        os.remove(temp_output_path)

                except Exception as e:
                    print(f"Error processing {input_video_path}: {str(e)}")
                    continue

                # Update the progress bar
                pbar.update(1)


if __name__ == "__main__":
    input_folder = input("Enter the input folder path: ")
    output_folder = input("Enter the output folder path: ")
    language_code = input("Enter the language code to remove (e.g., 'eng' for English): ")
    with_sub = input("Do you want to remove subtitles (y-yes, n-no)? ").strip().lower()

    process_videos_in_folder(input_folder, output_folder, language_code, with_sub)

input("end")
