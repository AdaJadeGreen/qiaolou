# 《楼·溯》第1章 巴丘瞭望 · 参考图生成提示词

用法：把对应组的 `02_参考图/G0x_xxx_2x2.png` 作为**参考图**上传到图像生成工具，粘贴「四宫格提示词」，生成干净的 2×2 参考图；
再把生成结果按格切成单体图，放回该组 `单体/` 下（命名 `{资产ID}_{名称}_重绘.png`），用于 Tripo 图生 3D。A 级资产可跳过重绘。

**通用要求（已写进每段提示词）**：纯白背景；每格一个物体，完整居中、无遮挡；3/4 俯视 15° 正侧角；无地面、无投影、无倒影；柔和均匀的影棚光；不加文字和水印；保持参考图中物体的外形、配色、材质与年代风格。

**统一风格描述**：东汉末年至三国（约公元210年）江南军营与水寨题材，写实游戏资产风格，风化旧木、粗麻布、暗红与深褐为主色，与《楼·溯》第1章巴丘瞭望总图一致。

## G01 船只

**四宫格提示词（中文）**

```
参考上传图片中的四个物体，生成一张 2×2 四宫格产品参考图，从左上到右下依次为：①画舫(带舱楼船)（深褐风化木船身，红漆木舱楼，卷檐小顶）；②双桅大帆船（双桅木帆船，竹篾硬帆半收，缆绳）；③单桅中帆船（单桅中型木帆船，硬帆收起）；④小木舟（无篷小木舟，船内堆缆绳，单杆）。每格只放一个物体，完整居中、互不遮挡，纯白背景，3/4 俯视角，无地面、无投影、无倒影，柔和均匀影棚光，写实游戏资产渲染风格，东汉末年至三国（约公元210年）江南军营与水寨题材，写实游戏资产风格，风化旧木、粗麻布、暗红与深褐为主色，与《楼·溯》第1章巴丘瞭望总图一致。保持参考图中各物体的外形比例、配色和材质，不要添加额外物体、文字或水印。
```

**Tripo 文生 3D 备用描述（英文，单体）**

- `CH01-SHP-01` 画舫(带舱楼船)：
  ```
  Small ornate Chinese river pleasure boat (huafang) with a red-lacquered wooden cabin and upturned roof eaves, dark weathered wooden hull, late Eastern Han dynasty China (c. 210 AD), realistic game asset, weathered materials, single object, no base, no ground
  ```
- `CH01-SHP-02` 双桅大帆船：
  ```
  Large two-masted ancient Chinese wooden sailing junk with battened bamboo-mat sails half furled, rigging ropes, dark brown hull, late Eastern Han dynasty China (c. 210 AD), realistic game asset, weathered materials, single object, no base, no ground
  ```
- `CH01-SHP-03` 单桅中帆船：
  ```
  Medium single-mast ancient Chinese wooden sailing boat with furled battened sail, late Eastern Han dynasty China (c. 210 AD), realistic game asset, weathered materials, single object, no base, no ground
  ```
- `CH01-SHP-04` 小木舟：
  ```
  Small open wooden rowing boat with coiled ropes inside and a single short mast pole, late Eastern Han dynasty China (c. 210 AD), realistic game asset, weathered materials, single object, no base, no ground
  ```

## G02 营地帐篷

**四宫格提示词（中文）**

```
参考上传图片中的四个物体，生成一张 2×2 四宫格产品参考图，从左上到右下依次为：①红顶主帐（红灰相间的大型军帐，木杆支撑，帐门半卷）；②灰白小帐（灰白麻布单坡帐，下摆垂地）；③双尖顶军帐（双尖顶深灰褐麻布军帐，木杆外露）；④营地货物木架（营地货物木架，搭布，挂杂物）。每格只放一个物体，完整居中、互不遮挡，纯白背景，3/4 俯视角，无地面、无投影、无倒影，柔和均匀影棚光，写实游戏资产渲染风格，东汉末年至三国（约公元210年）江南军营与水寨题材，写实游戏资产风格，风化旧木、粗麻布、暗红与深褐为主色，与《楼·溯》第1章巴丘瞭望总图一致。保持参考图中各物体的外形比例、配色和材质，不要添加额外物体、文字或水印。
```

**Tripo 文生 3D 备用描述（英文，单体）**

- `CH01-TNT-01` 红顶主帐：
  ```
  Large ancient Chinese military command tent, red and grey canvas, wooden poles, front flap half rolled up, late Eastern Han dynasty China (c. 210 AD), realistic game asset, weathered materials, single object, no base, no ground
  ```
- `CH01-TNT-02` 灰白小帐：
  ```
  Small off-white linen soldier tent with a sloped roof, hem touching the ground, late Eastern Han dynasty China (c. 210 AD), realistic game asset, weathered materials, single object, no base, no ground
  ```
- `CH01-TNT-03` 双尖顶军帐：
  ```
  Double-peaked dark grey-brown canvas army tent with exposed wooden poles, late Eastern Han dynasty China (c. 210 AD), realistic game asset, weathered materials, single object, no base, no ground
  ```
- `CH01-TNT-04` 营地货物木架：
  ```
  Rustic wooden camp supply rack draped with cloth, with sacks and hanging tools, late Eastern Han dynasty China (c. 210 AD), realistic game asset, weathered materials, single object, no base, no ground
  ```

## G03 远景地形

**四宫格提示词（中文）**

```
参考上传图片中的四个物体，生成一张 2×2 四宫格产品参考图，从左上到右下依次为：①远景主峰山脉（青灰远山主峰，带雾气层次）；②近岸山丘（临湖低矮山丘，植被覆盖）；③湖心岛群（湖面散落小岛，岩石+树丛）；④云层（积云/层云）。每格只放一个物体，完整居中、互不遮挡，纯白背景，3/4 俯视角，无地面、无投影、无倒影，柔和均匀影棚光，写实游戏资产渲染风格，东汉末年至三国（约公元210年）江南军营与水寨题材，写实游戏资产风格，风化旧木、粗麻布、暗红与深褐为主色，与《楼·溯》第1章巴丘瞭望总图一致。保持参考图中各物体的外形比例、配色和材质，不要添加额外物体、文字或水印。
```

**Tripo 文生 3D 备用描述（英文，单体）**

- `CH01-ENV-01` 远景主峰山脉：
  ```
  Distant blue-grey mountain range with a central peak, late Eastern Han dynasty China (c. 210 AD), realistic game asset, weathered materials, single object, no base, no ground
  ```
- `CH01-ENV-02` 近岸山丘：
  ```
  Low forested lakeside hill, late Eastern Han dynasty China (c. 210 AD), realistic game asset, weathered materials, single object, no base, no ground
  ```
- `CH01-ENV-03` 湖心岛群：
  ```
  Small rocky lake island with a few trees, late Eastern Han dynasty China (c. 210 AD), realistic game asset, weathered materials, single object, no base, no ground
  ```
- `CH01-ENV-04` 云层：
  ```
  Cumulus cloud bank, late Eastern Han dynasty China (c. 210 AD), realistic game asset, weathered materials, single object, no base, no ground
  ```

## G04 自然植被

**四宫格提示词（中文）**

```
参考上传图片中的四个物体，生成一张 2×2 四宫格产品参考图，从左上到右下依次为：①阔叶乔木（阔叶乔木，枝叶浓密，根部带土）；②常绿乔木（深绿常绿乔木，树冠饱满）；③景观山石（灰色风化山石，表面有苔藓）；④黄花灌木（开黄色小花的灌木丛）。每格只放一个物体，完整居中、互不遮挡，纯白背景，3/4 俯视角，无地面、无投影、无倒影，柔和均匀影棚光，写实游戏资产渲染风格，东汉末年至三国（约公元210年）江南军营与水寨题材，写实游戏资产风格，风化旧木、粗麻布、暗红与深褐为主色，与《楼·溯》第1章巴丘瞭望总图一致。保持参考图中各物体的外形比例、配色和材质，不要添加额外物体、文字或水印。
```

**Tripo 文生 3D 备用描述（英文，单体）**

- `CH01-VEG-01` 阔叶乔木：
  ```
  Broadleaf deciduous tree with a dense rounded green canopy and a soil clump at the roots, late Eastern Han dynasty China (c. 210 AD), realistic game asset, weathered materials, single object, no base, no ground
  ```
- `CH01-VEG-02` 常绿乔木：
  ```
  Evergreen tree with a full dark green canopy, late Eastern Han dynasty China (c. 210 AD), realistic game asset, weathered materials, single object, no base, no ground
  ```
- `CH01-VEG-03` 景观山石：
  ```
  Grey weathered landscape boulder with patches of moss, late Eastern Han dynasty China (c. 210 AD), realistic game asset, weathered materials, single object, no base, no ground
  ```
- `CH01-VEG-04` 黄花灌木：
  ```
  Low shrub covered in small yellow flowers, late Eastern Han dynasty China (c. 210 AD), realistic game asset, weathered materials, single object, no base, no ground
  ```

## G05 士兵

**四宫格提示词（中文）**

```
参考上传图片中的四个物体，生成一张 2×2 四宫格产品参考图，从左上到右下依次为：①蓝袍步卒（蓝色长袍步卒，兜鍪，腰佩刀）；②甲胄将官（灰黑甲胄将官，札甲，腰带）；③持枪士卒（灰蓝袍持枪士卒，皮甲）；④长枪甲士（长枪甲士，长袍外罩甲，枪杆高过头）。每格只放一个物体，完整居中、互不遮挡，纯白背景，3/4 俯视角，无地面、无投影、无倒影，柔和均匀影棚光，写实游戏资产渲染风格，东汉末年至三国（约公元210年）江南军营与水寨题材，写实游戏资产风格，风化旧木、粗麻布、暗红与深褐为主色，与《楼·溯》第1章巴丘瞭望总图一致。保持参考图中各物体的外形比例、配色和材质，不要添加额外物体、文字或水印。
```

**Tripo 文生 3D 备用描述（英文，单体）**

- `CH01-CHR-01` 蓝袍步卒：
  ```
  Han dynasty foot soldier in a long blue robe and helmet, sword at the waist, standing A-pose, late Eastern Han dynasty China (c. 210 AD), realistic game asset, weathered materials, single object, no base, no ground
  ```
- `CH01-CHR-02` 甲胄将官：
  ```
  Han dynasty officer in grey-black lamellar armor with a belt, standing A-pose, late Eastern Han dynasty China (c. 210 AD), realistic game asset, weathered materials, single object, no base, no ground
  ```
- `CH01-CHR-03` 持枪士卒：
  ```
  Han dynasty soldier in grey-blue robe and leather armor holding a spear, standing, late Eastern Han dynasty China (c. 210 AD), realistic game asset, weathered materials, single object, no base, no ground
  ```
- `CH01-CHR-04` 长枪甲士：
  ```
  Han dynasty armored spearman with a long spear taller than his head, standing, late Eastern Han dynasty China (c. 210 AD), realistic game asset, weathered materials, single object, no base, no ground
  ```

## G06 工匠百姓

**四宫格提示词（中文）**

```
参考上传图片中的四个物体，生成一张 2×2 四宫格产品参考图，从左上到右下依次为：①佩刀兵卒（灰蓝袍佩刀兵卒）；②灰衣工匠（灰衣工匠，短打，兜帽）；③褐衣百姓（褐色粗布袍百姓，头巾）；④褐衣劳工（褐衣劳工，挽袖，手持工具）。每格只放一个物体，完整居中、互不遮挡，纯白背景，3/4 俯视角，无地面、无投影、无倒影，柔和均匀影棚光，写实游戏资产渲染风格，东汉末年至三国（约公元210年）江南军营与水寨题材，写实游戏资产风格，风化旧木、粗麻布、暗红与深褐为主色，与《楼·溯》第1章巴丘瞭望总图一致。保持参考图中各物体的外形比例、配色和材质，不要添加额外物体、文字或水印。
```

**Tripo 文生 3D 备用描述（英文，单体）**

- `CH01-CHR-05` 佩刀兵卒：
  ```
  Han dynasty soldier in grey-blue robe with a sabre at the waist, standing A-pose, late Eastern Han dynasty China (c. 210 AD), realistic game asset, weathered materials, single object, no base, no ground
  ```
- `CH01-CHR-06` 灰衣工匠：
  ```
  Ancient Chinese craftsman in grey short work clothes and hood, full body, standing, late Eastern Han dynasty China (c. 210 AD), realistic game asset, weathered materials, single object, no base, no ground
  ```
- `CH01-CHR-07` 褐衣百姓：
  ```
  Ancient Chinese commoner in a brown coarse cloth robe and head scarf, full body, standing, late Eastern Han dynasty China (c. 210 AD), realistic game asset, weathered materials, single object, no base, no ground
  ```
- `CH01-CHR-08` 褐衣劳工：
  ```
  Ancient Chinese laborer in brown clothes with rolled sleeves holding a tool, full body, standing, late Eastern Han dynasty China (c. 210 AD), realistic game asset, weathered materials, single object, no base, no ground
  ```

## G07 旗帜木架

**四宫格提示词（中文）**

```
参考上传图片中的四个物体，生成一张 2×2 四宫格产品参考图，从左上到右下依次为：①东吴红色军旗（东吴暗红军旗，金色纹样，木横杆，燕尾下摆）；②黑色旗幡（黑底旗幡，暗色纹样，木架）；③大型兵器木架（大型木制兵器架/旗架，立杆交错）；④小型兵器木架（小型木栅兵器架）。每格只放一个物体，完整居中、互不遮挡，纯白背景，3/4 俯视角，无地面、无投影、无倒影，柔和均匀影棚光，写实游戏资产渲染风格，东汉末年至三国（约公元210年）江南军营与水寨题材，写实游戏资产风格，风化旧木、粗麻布、暗红与深褐为主色，与《楼·溯》第1章巴丘瞭望总图一致。保持参考图中各物体的外形比例、配色和材质，不要添加额外物体、文字或水印。
```

**Tripo 文生 3D 备用描述（英文，单体）**

- `CH01-FLG-01` 东吴红色军旗：
  ```
  Dark red Eastern Wu war banner with gold emblem, swallow-tail bottom edge, hung from a wooden crossbar on a tall pole, late Eastern Han dynasty China (c. 210 AD), realistic game asset, weathered materials, single object, no base, no ground
  ```
- `CH01-FLG-02` 黑色旗幡：
  ```
  Black banner with dark emblem hanging on a wooden frame pole, late Eastern Han dynasty China (c. 210 AD), realistic game asset, weathered materials, single object, no base, no ground
  ```
- `CH01-FLG-03` 大型兵器木架：
  ```
  Large wooden weapon and banner rack with crossed upright poles, late Eastern Han dynasty China (c. 210 AD), realistic game asset, weathered materials, single object, no base, no ground
  ```
- `CH01-FLG-04` 小型兵器木架：
  ```
  Small wooden slatted weapon rack, late Eastern Han dynasty China (c. 210 AD), realistic game asset, weathered materials, single object, no base, no ground
  ```

## G08 木箱木桶

**四宫格提示词（中文）**

```
参考上传图片中的四个物体，生成一张 2×2 四宫格产品参考图，从左上到右下依次为：①大木箱（深色风化大木箱，铁包角，盖板）；②铁箍木箱（浅褐铁箍木箱，绳索捆扎）；③小木箱（小木箱，带盖）；④木桶（木桶/大缸，铁箍）。每格只放一个物体，完整居中、互不遮挡，纯白背景，3/4 俯视角，无地面、无投影、无倒影，柔和均匀影棚光，写实游戏资产渲染风格，东汉末年至三国（约公元210年）江南军营与水寨题材，写实游戏资产风格，风化旧木、粗麻布、暗红与深褐为主色，与《楼·溯》第1章巴丘瞭望总图一致。保持参考图中各物体的外形比例、配色和材质，不要添加额外物体、文字或水印。
```

**Tripo 文生 3D 备用描述（英文，单体）**

- `CH01-PRP-01` 大木箱：
  ```
  Large dark weathered wooden storage chest with iron corner brackets and lid, late Eastern Han dynasty China (c. 210 AD), realistic game asset, weathered materials, single object, no base, no ground
  ```
- `CH01-PRP-02` 铁箍木箱：
  ```
  Light brown wooden crate with iron bands, tied with rope, late Eastern Han dynasty China (c. 210 AD), realistic game asset, weathered materials, single object, no base, no ground
  ```
- `CH01-PRP-03` 小木箱：
  ```
  Small wooden box with a lid, late Eastern Han dynasty China (c. 210 AD), realistic game asset, weathered materials, single object, no base, no ground
  ```
- `CH01-PRP-04` 木桶：
  ```
  Wooden barrel with iron hoops, late Eastern Han dynasty China (c. 210 AD), realistic game asset, weathered materials, single object, no base, no ground
  ```

## G09 马匹与杂项

**四宫格提示词（中文）**

```
参考上传图片中的四个物体，生成一张 2×2 四宫格产品参考图，从左上到右下依次为：①鞍马（枣红鞍马，皮鞍鞯，缰绳）；②木吊架（木制三脚吊架/绞架，挂绳钩）；③金属罐（铁/铜金属罐，带提梁）；④营地火盆（营地铁火盆/木墩炉）。每格只放一个物体，完整居中、互不遮挡，纯白背景，3/4 俯视角，无地面、无投影、无倒影，柔和均匀影棚光，写实游戏资产渲染风格，东汉末年至三国（约公元210年）江南军营与水寨题材，写实游戏资产风格，风化旧木、粗麻布、暗红与深褐为主色，与《楼·溯》第1章巴丘瞭望总图一致。保持参考图中各物体的外形比例、配色和材质，不要添加额外物体、文字或水印。
```

**Tripo 文生 3D 备用描述（英文，单体）**

- `CH01-ANM-01` 鞍马：
  ```
  Chestnut brown horse with a leather saddle, saddle cloth and bridle, standing side-on, late Eastern Han dynasty China (c. 210 AD), realistic game asset, weathered materials, single object, no base, no ground
  ```
- `CH01-PRP-05` 木吊架：
  ```
  Wooden tripod hoist frame with rope and hook, late Eastern Han dynasty China (c. 210 AD), realistic game asset, weathered materials, single object, no base, no ground
  ```
- `CH01-PRP-06` 金属罐：
  ```
  Small iron or bronze pot with a bail handle, late Eastern Han dynasty China (c. 210 AD), realistic game asset, weathered materials, single object, no base, no ground
  ```
- `CH01-PRP-07` 营地火盆：
  ```
  Iron camp fire brazier on short legs, late Eastern Han dynasty China (c. 210 AD), realistic game asset, weathered materials, single object, no base, no ground
  ```
