import os, random, subprocess, json, time, pathlib, urllib.request
import requests
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from PIL import Image, ImageDraw, ImageFont

BASE=pathlib.Path('/tmp/reggae_factory'); BASE.mkdir(exist_ok=True)
TREBLO='https://api.treblo.com/v1'
SCOPES=['https://www.googleapis.com/auth/youtube.upload']
SINGERS=['Jah River','Kairo Roots','Maya Kingston','Riddim Sage','Zion Blue','Nia Skies','Cedar Voice','Tafari Moon']
PRODUCERS=['Island Pulse','Roots Lab','Golden Dub Works','Kingston Signal','Coconut Yard','Sunset Riddim Co.']
WRITERS=['Marley Stone','Asha Reed','Caleb Rivers','Nia Clarke','Jaden Cole','Rohan James']
THEMES=['healing after heartbreak','summer love by the sea','keeping faith through hard times','one love and unity','late-night Kingston vibes','starting over with a smile','dancing through the rain','freedom and positive energy']

def make_prompt():
    singer=random.choice(SINGERS); producer=random.choice(PRODUCERS); writer=random.choice(WRITERS); theme=random.choice(THEMES)
    prompt=f"Original modern reggae song about {theme}. Warm Jamaican-inspired reggae groove, deep bass, skanking guitar, organic drums, tasteful dub space, memorable chorus, expressive original vocalist, radio-friendly but authentic, uplifting. Do not imitate or reference any specific real artist. Fictional singer: {singer}; fictional producer: {producer}; fictional writer: {writer}."
    return singer,producer,writer,theme,prompt

def treblo_generate(prompt):
    key=os.environ['TREBLO_API_KEY']; h={'Authorization':f'Bearer {key}','Content-Type':'application/json'}
    r=requests.post(f'{TREBLO}/generations/v3',headers=h,json={'prompt':prompt,'output_format':'mp3','output_bit_rate':192,'length_range':[150,240]},timeout=60); r.raise_for_status(); task=r.json()['task_id']
    for _ in range(180):
        s=requests.get(f'{TREBLO}/generations/status/{task}',headers={'Authorization':f'Bearer {key}'},timeout=30).json(); status=s if isinstance(s,str) else s.get('status')
        if status=='SUCCESS':
            g=requests.get(f'{TREBLO}/generations/{task}',headers={'Authorization':f'Bearer {key}'},timeout=30).json(); return task,g['song_paths'][0],g.get('lyrics','')
        if status=='FAILURE': raise RuntimeError(f'Treblo generation failed: {s}')
        time.sleep(5)
    raise TimeoutError('Treblo generation timed out')

def download(url,out):
    with requests.get(url,stream=True,timeout=120) as r:
        r.raise_for_status()
        with open(out,'wb') as f:
            for chunk in r.iter_content(1024*1024): f.write(chunk)

def make_art(title,singer,out):
    im=Image.new('RGB',(1920,1080)); d=ImageDraw.Draw(im); font='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'; f1=ImageFont.truetype(font,72); f2=ImageFont.truetype(font,42)
    d.text((100,410),title,font=f1,fill='white'); d.text((105,510),f'{singer} • Original Reggae',font=f2,fill='white'); d.text((105,900),'REGGAE MUSIC FACTORY',font=f2,fill='white'); im.save(out,quality=92)

def make_video(audio,image,out):
    cmd=['ffmpeg','-y','-loop','1','-i',image,'-i',audio,'-filter_complex','[1:a]aformat=channel_layouts=stereo,showwaves=s=1920x220:mode=line:rate=30,format=yuv420p[vwave];[0:v][vwave]overlay=0:780[v]','-map','[v]','-map','1:a','-c:v','libx264','-preset','veryfast','-tune','stillimage','-c:a','aac','-b:a','192k','-shortest','-pix_fmt','yuv420p',out]; subprocess.run(cmd,check=True)

def youtube_service():
    creds=Credentials(token=None,refresh_token=os.environ['YOUTUBE_REFRESH_TOKEN'],token_uri='https://oauth2.googleapis.com/token',client_id=os.environ['GOOGLE_CLIENT_ID'],client_secret=os.environ['GOOGLE_CLIENT_SECRET'],scopes=SCOPES)
    creds.refresh(Request()); return build('youtube','v3',credentials=creds)

def upload(video,title,description,tags):
    yt=youtube_service(); body={'snippet':{'title':title,'description':description,'tags':tags,'categoryId':'10','defaultLanguage':'en'},'status':{'privacyStatus':'private','selfDeclaredMadeForKids':False}}
    req=yt.videos().insert(part='snippet,status',body=body,media_body=MediaFileUpload(video,chunksize=8*1024*1024,resumable=True)); response=None
    while response is None: _,response=req.next_chunk()
    return response['id']

def main():
    singer,producer,writer,theme,prompt=make_prompt(); task,url,lyrics=treblo_generate(prompt); audio=BASE/'song.mp3'; art=BASE/'art.jpg'; video=BASE/'video.mp4'; download(url,audio)
    title=f'{theme.title()} — {singer} | Original Reggae'; make_art(title,singer,art); make_video(audio,art,video)
    desc=f'Original reggae music generated for Reggae Music Factory.\n\nSinger: {singer}\nProducer: {producer}\nWriter: {writer}\nTheme: {theme}\n\nThis is an original AI-generated musical work.'
    vid=upload(str(video),title,desc,['reggae','roots reggae','dancehall','jamaica','original music']); print(json.dumps({'youtube_video_id':vid,'title':title,'singer':singer,'producer':producer,'writer':writer,'task_id':task}))

if __name__=='__main__': main()
