from osgeo import gdal

class GTOPO30:
    def __init__(self):
        self.ds = gdal.Open("global_dem.vrt")
        self.gt = self.ds.GetGeoTransform()

    def toPixelCoords(self, lon, lat):
        gt = self.gt
        x = (lon - gt[0])/gt[1]
        y = (lat - gt[3])/gt[5]
        return (x,y)

    def toLatLon(self, x, y):
        gt = self.gt
        lat = gt[5]*y + gt[3]
        lon = gt[1]*x + gt[0]
        return (lat,lon)

    def getElevation(self, lon, lat):
        # proj is WGS84, so no reprojection/rotation necessary. Just use geo-transform.
        x0, y0 = self.toPixelCoords(lon,lat)
        return self.ds.ReadAsArray(x0,y0,1,1)[0][0]

    def getElevationArray(self, x0, y0, x1, y1):
        xSize = int(x1-x0)
        ySize = int(y1-y0)
        if x1<x0: x=x1
        else: x=x0
        if y1<y0: y=y1
        else: y=y0
        return {
            "array":self.ds.ReadAsArray(int(x),int(y),abs(xSize)+1,abs(ySize)+1),
            "x0":x,
            "y0":y
        }

    def getElevationProfile(self, lon0,lat0,lon1,lat1):
        pc0 = self.toPixelCoords(lon0,lat0)
        pc1 = self.toPixelCoords(lon1,lat1)
        points = self.bresenham(pc0, pc1)
        elev = self.getElevationArray(points[0][0],points[0][1],points[-1][0],points[-1][1])
        x0 = elev['x0']
        y0 = elev['y0']
        def getElev(x,y):
            x -= x0
            y -= y0
            z = elev['array'][int(y)][int(x)]
            if z == -9999: return 0
            else: return z
        return [(self.toLatLon(p[0],p[1])[1],self.toLatLon(p[0],p[1])[0],getElev(p[0],p[1])) for p in points]

    def bresenham(self, p0, p1):
        """
        Bresenham's algorithm for finding approximate grid cells that intersect line from point(x0,y0) to point(x1,y1)
        See https://en.wikipedia.org/wiki/Bresenham%27s_line_algorithm
        :param LatLon p0:
        :param LatLon p1:
        :return: [gridCell]
        """
        x0grid, y0grid = p0
        x1grid, y1grid = p1
        if y1grid>y0grid: yPositive = True
        else: yPositive = False
        if x1grid>x0grid: xPositive = True
        else: xPositive = False
        deltaxgrid = x1grid - x0grid
        if abs(deltaxgrid) < 1:  # this is a vertical line, just walk y vals
            if yPositive: yRange = range(int(y0grid), int(y1grid)+1)
            else: yRange = range(int(y1grid), int(y0grid)+1)
            return [(x0grid,y) for y in yRange]
        res=[]
        deltaygrid = y1grid - y0grid
        error = 0
        deltaerrgrid = abs (deltaygrid / deltaxgrid)    # Assume deltax != 0 (line is not vertical)
        y = int(y0grid)
        if xPositive: step = 1
        else: step = -1
        for x in range(int(x0grid),int(x1grid)+step,step):
            if (x,y) not in res: res.append((x,y))
            error = error + deltaerrgrid
            while error >= 0.5:
                 if (x,y) not in res: res.append((x,y))
                 if yPositive: y=int(y+1)
                 else: y=int(y-1)
                 error -=1.0
        return res

gtopo = GTOPO30()

def getElevation(lon,lat):
    """
    Gets elevation of point, from GTOPO30 elevation dataset.
    :param float lat: Latitude of POI
    :param float lon: Longitude of POI
    :return: Elevation, in meters, of point at lon,lat
    """
    if type(lat)==str: lat = float(lat)
    if type(lon)==str: lon = float(lon)
    return gtopo.getElevation(lon,lat)

def getElevationProfile(lon0,lat0,lon1,lat1):
    return gtopo.getElevationProfile(lon0,lat0,lon1,lat1)
