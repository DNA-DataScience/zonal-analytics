import uvicorn
from airport_api import app

if __name__ == "__main__":
    uvicorn.run("airport_api:app", host="0.0.0.0", port=8000, reload=True)


# QUERY = text('''
# SELECT
#     zone,
#     name,
#     type,
#     ST_AsBinary(
#         ST_Intersection(
#             ST_Transform(geometry, 3857),
#             ST_TileEnvelope(:z, :x, :y)
#         )
#     ) as geom
# FROM airport_layers
# WHERE ST_Intersects(
#     ST_Transform(geometry, 3857),
#     ST_TileEnvelope(:z, :x, :y)
# );
# ''')

# @app.get("/tiles/{z}/{x}/{y}.mvt")
# async def get_tile(z: int, x: int, y: int, db: Session = Depends(get_db)):
#     try:
#         result  = db.execute(QUERY, {"z": z, "x": x, "y": y})
#         rows = result.fetchall()
        
#         db.close()
        
#         if not rows:
#             return Response(content=b'', media_type="application/vnd.mapbox-vector-tile")
        
#         features = []
#         for row in rows:
            
#             zone = row[0]
#             name = row[1]
#             type_val = row[2]
#             geom_data = row[3]
            
#             # if isinstance(row.geom, str):
#             #     geom = wkb.loads(row.geom, hex=True)
#             # else:
#             #     geom = wkb.loads(bytes(row.geom))
                
#             geom = wkb.loads(bytes(geom_data))
                
#             simplification_levels = {
#                 0: 1000,
#                 5: 100,
#                 10: 10,
#                 14: 1,
#             }
            
#             tolerance = simplification_levels.get(z, 10)
#             simplified_geom = geom.simplify(tolerance, preserve_topology=False)
            
#             feature = {
#                 "geometry": mapping(simplified_geom),
#                 "properties": {
#                     "zone": str(zone),
#                     "name": str(name),
#                     "type": str(type_val),
#                 }
#             }
#             features.append(feature)
        
#         tile_data = mapbox_vector_tile.encode(
#             {
                
#                 "name": "airport_layers",
#                 "features": features
#             }
#         )
        
#         compressed = gzip.compress(tile_data)
        
#         return Response(
#             content= compressed,
#             media_type= "application/vnd.mapbox-vector-tile",
#             headers={"Content-Encoding": "gzip"}
#         )
        
#     except Exception as e:
#         import traceback
#         import sys
        
#         # Get full traceback as string
#         tb_str = traceback.format_exc()
        
#         # Print to console
#         print(tb_str)
        
#         # Or log it
#         # logger.error(tb_str)
        
#         raise HTTPException(status_code=500, detail=str(e))
