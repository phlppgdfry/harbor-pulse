"""macOS CLI narration + ffmpeg; uses evidence slides, no Power BI capture."""
import json,pathlib,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[1];D=ROOT/'build/video';OUT=ROOT/'docs/assets'
texts=[
'Harbor Pulse asks how a terminal operator could reduce delay without moving queues or overstating savings. This portfolio case uses a fictional terminal network and a synthetic year of data. It connects operational reporting to an explicit investment decision.',
'Trust starts with the denominator. The pipeline skips two hundred sixteen duplicate events, audits thirty six late revisions, and retains invalid records in quarantine. Missing departure records remain visible through coverage. Vehicle totals reconcile independently from sources to daily facts.',
'The investment comparison separates recurring operating cost from one off implementation cost. Only a usable fraction of saved waiting time receives financial value. Under the invented assumptions, dispatch and appointment slots are the first option to pilot, rather than immediately roll out.',
'The sensitivity analysis includes zero benefit and shows how realizable savings change annual value and first year cash. Regression diagnostics examine residuals, correlated inputs and a chronological holdout. These associations describe generated data. They do not identify the causal effect of staffing.',
'The simulated pilot randomizes lanes within day blocks. It uses paired day inference and checks smaller effects, null results, missing days and spillover. Its apparent improvement is simulated. A real pilot needs pre agreed guardrails, suitable assignment, real variability and measured resource redeployment.',
'The public case exposes Python, SQL, DAX, tests and operating evidence. You can reproduce the core without a Microsoft account. Philippe Godfroy developed this portfolio with AI assistance. These charts are reproducible analysis figures, not Power BI screenshots or evidence of actual business impact.'
]
for i,text in enumerate(texts):
 (D/f'narration-{i}.txt').write_text(text)
 subprocess.run(['say','-v','Samantha','-r','165','-o',str(D/f'audio-{i}.aiff'),'-f',str(D/f'narration-{i}.txt')],check=True)
 duration=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','default=noprint_wrappers=1:nokey=1',str(D/f'audio-{i}.aiff')],text=True))
 if duration>20:raise RuntimeError(f'Narration {i} exceeds slide duration: {duration}')
 subprocess.run(['ffmpeg','-y','-loglevel','error','-loop','1','-i',str(D/f'slide-{i}.png'),'-i',str(D/f'audio-{i}.aiff'),'-t','20','-r','24','-c:v','libx264','-preset','fast','-crf','26','-pix_fmt','yuv420p','-af','apad','-c:a','aac','-b:a','96k',str(D/f'part-{i}.mp4')],check=True)
(D/'concat.txt').write_text(''.join(f"file '{D}/part-{i}.mp4'\n" for i in range(6)))
subprocess.run(['ffmpeg','-y','-loglevel','error','-f','concat','-safe','0','-i',str(D/'concat.txt'),'-c','copy','-movflags','+faststart',str(OUT/'harbor-pulse-walkthrough.mp4')],check=True)
def stamp(seconds):return f'00:{seconds//60:02d}:{seconds%60:02d}.000'
(OUT/'walkthrough-en.vtt').write_text('WEBVTT\n\n'+''.join(f'{i+1}\n{stamp(i*20)} --> {stamp((i+1)*20)}\n{text}\n\n' for i,text in enumerate(texts)).rstrip()+'\n')
(ROOT/'docs/VIDEO-TRANSCRIPT.md').write_text('# Two-minute walkthrough transcript\n\nNarration is synthesized. All charts are independently rendered synthetic analysis figures, not Power BI screenshots.\n\n'+ '\n\n'.join(f'**{i*20//60}:{i*20%60:02d}** {text}' for i,text in enumerate(texts)))
print('Generated 120-second narrated walkthrough with captions')
