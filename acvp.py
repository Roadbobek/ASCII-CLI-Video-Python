import cv2
from ascii_magic import AsciiArt, Back
import time
import os
from moviepy import VideoFileClip
from playsound3 import playsound
import sys

def video_to_ascii_cli(video_path, columns=80):
    """
    Converts a video file to ASCII art and plays its audio in the terminal.

    Args:
        video_path (str): The path to the video file.
        columns (int): The number of columns for the ASCII art output.
    """
    # Create Temp folder if it doesn't exist
    temp_dir = "Temp"
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
        print(f"Created {temp_dir} directory for temporary files")

    audio_path = None
    video_clip = None
    try:
        print(f"Loading video file: {video_path}")
        video_clip = VideoFileClip(video_path)
        print(f"Video loaded successfully. Duration: {video_clip.duration}s")

        # Check if video has audio
        print(f"Checking for audio track...")
        if video_clip.audio is not None:
            print(f"Audio track found! Audio duration: {video_clip.audio.duration}s")

            # Extract audio to Temp folder with proper naming
            video_name = os.path.splitext(os.path.basename(video_path))[0]
            audio_path = os.path.join(temp_dir, f"{video_name}_audio.mp3")

            print(f"Extracting audio to: {audio_path}")

            # Remove existing audio file if it exists
            if os.path.exists(audio_path):
                os.remove(audio_path)
                print(f"Removed existing audio file: {audio_path}")

            # Extract audio with simplified and more reliable approach
            try:
                print("Starting audio extraction...")
                if not os.path.exists(temp_dir):
                    os.makedirs(temp_dir)
                    print(f"Created temp directory: {temp_dir}")

                try:
                    print(f"Extracting audio using working method...")
                    video_clip.audio.write_audiofile(
                        audio_path,
                        codec='mp3',
                        bitrate='128k'
                    )
                    print("Audio extraction completed successfully")
                except Exception as extraction_error:
                    print(f"Primary extraction failed: {extraction_error}")

                    # Fallback to WAV if MP3 fails
                    try:
                        wav_audio_path = audio_path.replace('.mp3', '.wav')
                        print(f"Trying WAV extraction to: {wav_audio_path}")
                        video_clip.audio.write_audiofile(wav_audio_path)
                        audio_path = wav_audio_path
                        print("WAV audio extraction completed successfully")
                    except Exception as wav_error:
                        print(f"WAV extraction also failed: {wav_error}")
                        audio_path = None

            except Exception as audio_extract_error:
                print(f"Error during audio extraction: {audio_extract_error}")
                import traceback
                traceback.print_exc()
                audio_path = None

            # Verify the audio file was created successfully
            if audio_path and os.path.exists(audio_path):
                file_size = os.path.getsize(audio_path)
                print(f"Audio extracted successfully: {audio_path} ({file_size} bytes)")

                if file_size > 0:
                    try:
                        with open(audio_path, 'rb') as f:
                            f.read(1)  # Try to read first byte
                        print(f"Audio file verified and accessible")
                    except Exception as file_error:
                        print(f"Error accessing audio file: {file_error}")
                        audio_path = None
                else:
                    print(f"Audio file is empty (0 bytes)")
                    audio_path = None
            else:
                print(f"Error: Audio file was not created at {audio_path}")
                if os.path.exists(temp_dir):
                    print(f"Contents of {temp_dir}:")
                    for item in os.listdir(temp_dir):
                        item_path = os.path.join(temp_dir, item)
                        if os.path.isfile(item_path):
                            size = os.path.getsize(item_path)
                            print(f"  - {item} ({size} bytes)")
                        else:
                            print(f"  - {item} (directory)")
                else:
                    print(f"Temp directory {temp_dir} does not exist")
                audio_path = None
        else:
            print("No audio track found in the video file.")

    except Exception as e:
        print(f"Error loading or processing video: {e}")
        import traceback
        traceback.print_exc()
        audio_path = None
    finally:
        if video_clip:
            video_clip.close()
            print("Video clip closed")

    # --- Video to ASCII Conversion ---
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Could not open video file {video_path}")
        return

    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    if fps > 0:
        target_frame_delay = 1.0 / fps
    else:
        target_frame_delay = 1.0 / 30  # Default to 30 FPS if unable to detect

    print(f"Video FPS: {fps}, Target frame delay: {target_frame_delay:.4f}s")
    print("Starting video to ASCII conversion. Press Ctrl+C to stop.")

    frame_count = 0
    start_time = time.time()
    expected_time = start_time

    # Pre-clear screen once
    os.system('cls' if os.name == 'nt' else 'clear')

    # Play audio using playsound with block=False
    if audio_path:
        try:
            print("Starting audio playback (non-blocking)...")
            # playsound will return immediately, audio plays in background
            playsound(audio_path, block=False)
            print("Audio playback initiated.")
        except Exception as e:
            print(f"Audio playback error with block=False: {e}")

    try:
        while cap.isOpened():
            frame_start = time.time()

            ret, frame = cap.read()
            if not ret:
                # print("End of video reached.") # DEBUG
                break

            # Convert frame to ASCII
            try:
                height, width = frame.shape[:2]
                if width > 640:
                    scale = 640 / width
                    new_width = int(width * scale)
                    new_height = int(height * scale)
                    frame = cv2.resize(frame, (new_width, new_height))

                ascii_image = AsciiArt.from_array(frame)
                temp_frame_path = None
            except AttributeError:
                temp_frame_path = os.path.join(temp_dir, "temp_frame.png")
                cv2.imwrite(temp_frame_path, frame)
                ascii_image = AsciiArt.from_image(temp_frame_path)
            except Exception as e:
                print(f"Unexpected error converting frame: {e}. Skipping frame.")
                frame_count += 1
                continue

            print('\033[H', end='')  # Move cursor to home position
            ascii_image.to_terminal(columns=min(columns, 100))

            if temp_frame_path and os.path.exists(temp_frame_path):
                os.remove(temp_frame_path)

            frame_count += 1

            frame_end = time.time()
            processing_time = frame_end - frame_start

            target_next_frame_time = start_time + (frame_count * target_frame_delay)
            current_time = time.time()

            sleep_time = target_next_frame_time - current_time
            if sleep_time > 0:
                time.sleep(sleep_time)
            elif sleep_time < -target_frame_delay:
                frames_to_skip = int(abs(sleep_time) / target_frame_delay)
                for _ in range(min(frames_to_skip, 3)):
                    ret, _ = cap.read()
                    if not ret:
                        break
                    frame_count += 1

    except KeyboardInterrupt:
        print("\nVideo playback interrupted by user.")
    except Exception as e:
        print(f"Error during video playback: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cap.release()

        # Clean up temporary audio file
        if audio_path and os.path.exists(audio_path):
            try:
                os.remove(audio_path)
                # print(f"Cleaned up temporary audio file: {audio_path}")  # DEBUG
            except Exception as e:
                print(f"Error cleaning up audio file: {e}")

        # print("Video to ASCII conversion finished.") # DEBUG


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python acvp.py <video_path>")
        print("Example: python acvp.py Videos/peak.mp4")
        sys.exit(1)

    video_path = sys.argv[1]
    video_to_ascii_cli(video_path)