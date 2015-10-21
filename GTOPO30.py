from osgeo import gdal

class GTOPO30:
    def __init__(self):
        self.ds = gdal.Open("global_dem.vrt")

    def getElevation(self,lon,lat):
         # proj is WGS84, so no reprojection/rotation necessary. Just use geo-transform.
        gt = self.ds.GetGeoTransform()
        x = int((lon-gt[0])/gt[1])
        y = int((lat-gt[3])/gt[5])
        return self.ds.ReadAsArray(x,y,1,1)[0][0]

    def getElevationProfile(self, p0, p1):
        points = self.bresenham(p0, p1)
        return [(p[0],p[1],getElevation(p[0],p[1])) for p in points]

    def bresenham(self, p0, p1):
        """
        Bresenham's algorithm for finding approximate grid cells that intersect line from point(x0,y0) to point(x1,y1)
        See https://en.wikipedia.org/wiki/Bresenham%27s_line_algorithm
        :param LatLon p0:
        :param LatLon p1:
        :return: [gridCell]
        """
        x0 = -180
        y0 = 90
        dy = -1/120.
        dx = 1/120.
        y0grid = ( p0.lat.decimal_degree / dy ) - ( y0 / dy )
        y1grid = ( p1.lat.decimal_degree / dy ) - ( y0 / dy )
        x0grid = ( p0.lon.decimal_degree / dx ) - ( x0 / dx )
        x1grid = ( p1.lon.decimal_degree / dx ) - ( x0 / dx )
        if y1grid>y0grid: yPositive = True
        else: yPositive = False
        if x1grid>x0grid: xPositive = True
        else: xPositive = False
        deltaxgrid = x1grid - x0grid
        if abs(deltaxgrid) < 1:  # this is a vertical line, just walk y vals
            if yPositive: yRange = range(int(y0grid), int(y1grid)+1)
            else: yRange = range(int(y1grid), int(y0grid)+1)
            return [(x0grid*dx-180,y*dy+90) for y in yRange]
        res=[]
        deltaygrid = y1grid - y0grid
        error = 0
        deltaerrgrid = abs (deltaygrid / deltaxgrid)    # Assume deltax != 0 (line is not vertical)
        y = int(y0grid)
        # if xPositive: xRange = range(int(x0grid),int(x1grid))
        # else: xRange = range(int(x1grid),int(x0grid))
        if xPositive: step = 1
        else: step = -1
        for x in range(int(x0grid),int(x1grid)+step,step):
            if (x,y) not in res: res.append((x*dx-180,y*dy+90))
            error = error + deltaerrgrid
            while error >= 0.5:
                 if (x,y) not in res: res.append((x*dx-180,y*dy+90))
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

def getElevationProfile(p0,p1):
    return gtopo.getElevationProfile(p0,p1)
