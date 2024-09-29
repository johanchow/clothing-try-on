import replicate
from helper.resource import copy_resource_to_cos

def requestReplicate(id, input):
    output = replicate.run(id, input=input)
    return output

def request_fooocus_try_on(text_prompt, clothing_url):
  print("fooocus text_prompt: ", text_prompt)
  print("fooocus image_prompt url: ", clothing_url)
  input = {
      "prompt": text_prompt,
      "style_selections": "Fooocus V2,Fooocus Enhance,Fooocus Sharp,Fooocus Masterpiece,Fooocus Photograph",
      "image_number": 1,
      "aspect_ratios_selection": "832*1216",
      "performance_selection": "Quality",
      "negative_prompt": "sexy, porn",
      "image_seed": 150,
      "cn_img1": clothing_url,
      "cn_stop1": 0.85,
      "cn_weight1": 0.98,
      "cn_type1": "ImagePrompt"
  }
  output = replicate.run(
     "konieshadow/fooocus-api:fda927242b1db6affa1ece4f54c37f19b964666bf23b0d06ae2439067cd344a4",
      input=input
  )
  print("fooocus output: ", output)
  id, url = copy_resource_to_cos(output[0])
  return url


