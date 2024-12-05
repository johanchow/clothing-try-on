import replicate
from helper.resource import copy_resource_to_cos
from helper.logger import logger

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
      "mrhan1993/fooocus-api:bd7d45104209dc3e1e2765d364697f1393a92a210a0e47fdf943afbd2271a48c",
    #  "konieshadow/fooocus-api:fda927242b1db6affa1ece4f54c37f19b964666bf23b0d06ae2439067cd344a4",
      input=input
  )
  print("fooocus output: ", output)
  id, url = copy_resource_to_cos(output[0])
  return url

def request_idm_vton(human_url, clothing_url, clothing_category):
  logger.info(f'idm-vton: human_url: {human_url}, clothing_url: {clothing_url}, category: {clothing_category}')
  try:
    output = replicate.run(
      "cuuupid/idm-vton:c871bb9b046607b680449ecbae55fd8c6d945e0a1948644bf2361b3d021d3ff4",
      input={
          "crop": False,
          "seed": 42,
          "steps": 30,
          # "upper_body", "lower_body", "dresses"
          "category": clothing_category,
          "force_dc": False,
          "garm_img": clothing_url,
          "human_img": human_url,
          "mask_only": False,
          "garment_des": ""
      }
    )
  except Exception as e:
    error_message = str(e) if e is not None else "Unknown"
    logger.error(f"replicate call error: {error_message}")
    return ""
  print(output)
  id, url = copy_resource_to_cos(output)
  return url

