import streamlit as st, requests, time

st.title("ComfyUI Generator")

p=st.text_input("Prompt")

if st.button("Generate"):
 r=requests.post("http://localhost:8000/gen",json={"prompt":p}).json()
 j=r["job"]
 for _ in range(60):
  res=requests.get(f"http://localhost:8000/res/{j}").json()
  if res.get("status")=="done":
   img=f"http://localhost:8188/view?filename={res['file']}&type=output"
   st.image(img); break
  time.sleep(2)