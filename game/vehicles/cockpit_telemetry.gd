extends RefCounted

# A tiny original bitmap instrument font. One CPU texture at 10 Hz, no extra
# viewport, camera, lights, or per-frame text meshes.
const FONT := {
"0":[14,17,19,21,25,17,14],"1":[4,12,4,4,4,4,14],"2":[14,17,1,2,4,8,31],
"3":[30,1,1,14,1,1,30],"4":[2,6,10,18,31,2,2],"5":[31,16,16,30,1,1,30],
"6":[14,16,16,30,17,17,14],"7":[31,1,2,4,8,8,8],"8":[14,17,17,14,17,17,14],
"9":[14,17,17,15,1,1,14],"A":[14,17,17,31,17,17,17],"B":[30,17,17,30,17,17,30],
"C":[14,17,16,16,16,17,14],"D":[30,17,17,17,17,17,30],"E":[31,16,16,30,16,16,31],
"F":[31,16,16,30,16,16,16],"G":[14,17,16,23,17,17,15],"H":[17,17,17,31,17,17,17],
"I":[14,4,4,4,4,4,14],"J":[7,2,2,2,18,18,12],"K":[17,18,20,24,20,18,17],
"L":[16,16,16,16,16,16,31],"M":[17,27,21,21,17,17,17],"N":[17,25,25,21,19,19,17],
"O":[14,17,17,17,17,17,14],"P":[30,17,17,30,16,16,16],"Q":[14,17,17,17,21,18,13],
"R":[30,17,17,30,20,18,17],"S":[15,16,16,14,1,1,30],"T":[31,4,4,4,4,4,4],
"U":[17,17,17,17,17,17,14],"V":[17,17,17,17,17,10,4],"W":[17,17,17,21,21,21,10],
"X":[17,17,10,4,10,17,17],"Y":[17,17,10,4,4,4,4],"Z":[31,1,2,4,8,16,31],
"/":[1,2,2,4,8,8,16],"-":[0,0,0,31,0,0,0],".":[0,0,0,0,0,12,12],
"%":[17,2,4,8,16,17,0]," ":[0,0,0,0,0,0,0]
}
var image := Image.create(512,192,false,Image.FORMAT_RGBA8)
var texture: ImageTexture
var last_speed := -1
var last_mode := ""
const CYAN := Color("76dce5")
const DIM := Color("375968")
const WHITE := Color("d7f7f5")
const AMBER := Color("f2a35b")

func _init() -> void:
	texture = ImageTexture.create_from_image(image)
	update(0,0,0,0)

func rect(x: int,y: int,w: int,h: int,color: Color) -> void:
	image.fill_rect(Rect2i(x,y,w,h),color)

func text(x: int,y: int,value: String,scale: int,color: Color) -> void:
	for letter in value:
		var rows: Array = FONT.get(letter,FONT[" "])
		for row in range(7):
			for col in range(5):
				if int(rows[row]) & (1 << (4-col)):
					rect(x+col*scale,y+row*scale,scale,scale,color)
		x+=6*scale

func update(speed: float, thrust: float, steer: float, slip: float, boosting: bool = false, charge: float = 100.0) -> void:
	image.fill(Color("07151e"))
	last_speed = int(absf(speed)*3.6)
	last_mode = "BOOST" if boosting else "REVERSE" if speed < -0.05 else ("DRIVE" if absf(speed)>0.1 else "HOLD")
	text(12,9,"KESTREL / MK I",2,CYAN)
	text(370,9,last_mode,2,AMBER)
	rect(12,31,488,1,DIM)
	rect(174,42,1,116,DIM)
	rect(342,42,1,116,DIM)
	text(14,43,"SPEED",2,CYAN)
	text(12,69,"%03d"%last_speed,8,WHITE)
	text(14,138,"KM/H",2,CYAN)
	text(190,43,"REPULSORS",2,CYAN)
	# Four indicated loads respond to thrust and steering demand.
	for i in range(4):
		var px := 194+(i%2)*98
		var py := 73+(i/2)*47
		rect(px,py,32,32,DIM)
		rect(px+2,py+2,28,28,Color("0c2631"))
		var load := clampf(0.45+thrust*0.35+steer*(0.15 if i%2==0 else -0.15),0,1)
		var level := int(24*load)
		rect(px+5,py+27-level,22,level,CYAN)
	text(238,93,"H",4,WHITE)
	text(358,43,"DRIVE",2,CYAN)
	rect(358,72,140,18,DIM)
	rect(360,74,int(136*thrust),14,AMBER)
	text(358,102,"%03d"%int(thrust*100),3,WHITE)
	text(424,109,"PWR",2,AMBER)
	text(358,140,"SLIP %02d"%mini(99,int(slip*100)),2,CYAN)
	rect(12,165,488,1,DIM)
	text(14,174,"VECTOR",1,CYAN)
	rect(65,175,106,5,DIM)
	rect(116+int(steer*48),173,5,9,AMBER)
	text(192,174,"MAGNETIC HOLD" if last_mode=="HOLD" else "VECTOR ACTIVE",1,CYAN)
	text(372,174,"CAP %03d"%int(charge),1,AMBER if boosting else CYAN)
	texture.update(image)
