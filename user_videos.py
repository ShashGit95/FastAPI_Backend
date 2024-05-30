import torch
from diffusers import DiffusionPipeline, DPMSolverMultistepScheduler
from diffusers.utils import export_to_video
from PIL import Image
from fastapi import HTTPException, Response
from models import Video
import os



output_folder_path = 'static/output_video'

# Generate videos 
async def create_video(text_prompt: str, user_id: int, db):

    global video_frames
    prompt = text_prompt

    # Customize the output name
    vid_name_1 = 'before_upscale'

    # Create pipeline
    pipe = DiffusionPipeline.from_pretrained("cerspense/zeroscope_v2_576w", torch_dtype=torch.float16)

     # Optimize for GPU memory
    # if torch.cuda.is_available():
    pipe.enable_model_cpu_offload()
        
    # Create video
    pipe.unet.enable_forward_chunking(chunk_size=1, dim=1)
    pipe.enable_vae_slicing()

    video_duration_seconds = 3
    num_frames = video_duration_seconds * 8
    # Set output path
    output_name = f'{output_folder_path}/{vid_name_1}.mp4'  
    video_frames = pipe(prompt, num_inference_steps=40, height=320, width=576, num_frames=num_frames).frames
    video_frames = video_frames.reshape(-1, 320, 576, 3)
    video_path = export_to_video(video_frames, output_video_path=output_name)

    # Save video metadata to the database
    # db = next(get_db())  # Get the DB session; adjust according to how you manage database sessions
    db = db
    new_video = Video(user_id=user_id, video_path=video_path)
    db.add(new_video)
    db.commit()
    db.refresh(new_video)

    return video_path



# download video
async def start_download_video(video_url: str):

    if not video_url:
        raise HTTPException(status_code=400, detail="Video URL is missing or empty.")

    # Assuming the video is stored in the local filesystem
    video_path = video_url  # Assuming video_url contains the path to the video

    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="Video not found.")

    # Set content disposition to attachment to force download
    headers = {
        "Content-Disposition": f"attachment; filename={os.path.basename(video_path)}"
    }

    return Response(content=open(video_path, 'rb'), headers=headers, media_type='video/mp4')
