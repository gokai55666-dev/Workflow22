def build(p):
 return {
  "1":{"inputs":{"ckpt_name":"dreamshaper_8.safetensors"},"class_type":"CheckpointLoaderSimple"},
  "2":{"inputs":{"width":1024,"height":1024,"batch_size":1},"class_type":"EmptyLatentImage"},
  "3":{"inputs":{"text":p,"clip":["1",1]},"class_type":"CLIPTextEncode"},
  "4":{"inputs":{"text":"bad, blurry","clip":["1",1]},"class_type":"CLIPTextEncode"},
  "5":{"inputs":{"seed":0,"steps":30,"cfg":7,"sampler_name":"euler","scheduler":"normal","model":["1",0],"positive":["3",0],"negative":["4",0],"latent_image":["2",0]},"class_type":"KSampler"},
  "6":{"inputs":{"samples":["5",0],"vae":["1",2]},"class_type":"VAEDecode"},
  "7":{"inputs":{"filename_prefix":"bot","images":["6",0]},"class_type":"SaveImage"}
 }