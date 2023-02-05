from sanic import Sanic, Blueprint
from sanic.response import json, redirect
from sanic_ext import render
import requests, base64, json as jsonm, os

def APIError(code: str):
	if code == 1:
		status_code = 404
		message = "Invalid Player UUID"
		error = "INVALID_PLAYER_UUID"
	else:
		status_code = 500
		message = "Unable to generate error trace!"
		error = "CANNOT_GENERATE_TRACE"
	return json({
		"code": code,
		"status_code": 500,
		"message": message,
		"error": error
	})

def getPlayerTexture(session_data: dict):
	properties = session_data.get("properties")
	texture_value = None
	for mcproperty in properties:
		if mcproperty.get("name") == "textures":
			texture_value = mcproperty.get("value")
			break
	texture_value = jsonm.loads(base64.b64decode(texture_value))
	texture = texture_value.get("textures")
	texture = texture.get("SKIN")
	texture = texture.get("url")
	return texture

def getPlayerData(player_name: str):
	uuid = requests.get(mojangapi+"users/profiles/minecraft/"+player_name).json()['id']
	return getPlayerDataUUID(uuid)

def getPlayerDataUUID(player_uuid: str):
	data = requests.get(minecraftsessionapi+"session/minecraft/profile/"+player_uuid).json()
	return {
		"username": data.get("name"),
		"uuid": data.get("id"),
		"skin_url": getPlayerTexture(data),
		"card_url": f"https://minemc.beecrew.uk.to/p/{data.get('name')}?card=true"
	}

app = Sanic(__name__)
app.config["dev"] = False
if app.config["dev"]:
	port = 3000
else:
	port = os.environ.get("PORT")
mojangapi = "https://api.mojang.com/"
minecraftsessionapi = "https://sessionserver.mojang.com/"
app.static("/assets", "./assets")
main = Blueprint("main")
api = Blueprint("api", url_prefix="/api")

#Main Website
@main.get("/")
async def home(request):
	return await render("index.html")

@main.get("/about")
async def about(request):
	return await render("about.html")

@main.get("/p/<player_name>")
async def player(request, player_name):
	isCard = request.args.get("card")
	player_data = getPlayerData(player_name)
	context = {"player": player_data}
	if (isCard):
		return await render("playercard.html", context=context)
	else:
		return await render("player.html", context=context)

#API Stuff
@api.get("/player_data")
async def api_player_data(request):
	uuid = request.args.get("uuid")
	if uuid:
		return json(getPlayerDataUUID(uuid))
	else:
		return APIError(1)

@api.get("/player_skin")
async def api_player_skin(request):
	uuid = request.args.get("uuid")
	if uuid:
		player_data = getPlayerDataUUID(uuid)
		return redirect(player_data['skin_url'])
	else:
		return APIError(1)

app.blueprint(api)
app.blueprint(main)
if __name__ == "__main__":
	app.run(port=port, dev=app.config["dev"])