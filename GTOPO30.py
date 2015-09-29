from osgeo import gdal

class GTOPO30:
    filenames = [
        ["W180N90.DEM","W140N90.DEM","W100N90.DEM","W060N90.DEM","W020N90.DEM","E020N90.DEM","E060N90.DEM","E100N90.DEM","E140N90.DEM"],
        ["W180N40.DEM","W140N40.DEM","W100N40.DEM","W060N40.DEM","W020N40.DEM","E020N40.DEM","E060N40.DEM","E100N40.DEM","E140N40.DEM"],
        ["W180S10.DEM","W140S10.DEM","W100S10.DEM","W060S10.DEM","W020S10.DEM","E020S10.DEM","E060S10.DEM","E100S10.DEM","E140S10.DEM"],
        ["W180S60.DEM","W120S60.DEM","W060S60.DEM","W000S60.DEM","E060S60.DEM","E120S60.DEM"]
    ]
    dxS60 = 60

    x0 = -180
    y0 = 90
    dx = 40
    dy = -50

    datasets=[
        [False for x in range(9)],
        [False for x in range(9)],
        [False for x in range(9)],
        [False for x in range(6)]
    ]

    def getDataset(self,lon,lat):
        y = int((lat-self.y0)/self.dy)
        if lat > -60:
            x = int((lon-self.x0)/self.dx)
        else:
            x = int((lon-self.x0)/self.dxS60)
        if self.datasets[y][x] == False:
            self.datasets[y][x] = gdal.Open("data/"+self.filenames[y][x])
        return self.datasets[y][x]

    def getElevation(self,lon,lat):
        ds = self.getDataset(lon,lat)
         # proj is WGS84, so no reprojection/rotation necessary. Just use geo-transform.
        gt = ds.GetGeoTransform()
        x = int((lon-gt[0])/gt[1])
        y = int((lat-gt[3])/gt[5])
        return ds.ReadAsArray(x,y,1,1)[0][0]

    def getElevationProfile(self,x0, y0, x1, y1):
        points = self.bresenham(x0, y0, x1, y1)
        return [(p[0],p[1],getElevation(p[0],p[1])) for p in points]

    def bresenham(self, x0, y0, x1, y1):
        """
        Bresenham's algorithm for finding approximate grid cells that intersect line from point(x0,y0) to point(x1,y1)
        See https://en.wikipedia.org/wiki/Bresenham%27s_line_algorithm
        :param int x0:
        :param int y0:
        :param int x1:
        :param int y1:
        :return: [gridCell]
        """
        dy = -1/120.
        dx = 1/120.
        y0grid = ( y0 / dy ) - ( self.y0 / dy )
        y1grid = ( y1 / dy ) - ( self.y0 / dy )
        x0grid = ( x0 / dx ) - ( self.x0 / dx )
        x1grid = ( x1 / dx ) - ( self.x0 / dx )
        if y1grid>y0grid: yPositive = True
        else: yPositive = False
        if x1grid>x0grid: xPositive = True
        else: xPositive = False
        deltaxgrid = x1grid - x0grid
        if deltaxgrid == 0:  # this is a vertical line, just walk y vals
            if yPositive: yRange = range(int(y0grid), int(y1grid))
            else: yRange = range(int(y1grid), int(y0grid))
            return [(x0grid*dx,y*dy) for y in yRange]
        res=[]
        deltaygrid = y1grid - y0grid
        error = 0
        deltaerrgrid = abs (deltaygrid / deltaxgrid)    # Assume deltax != 0 (line is not vertical)
        y = int(y0grid)
        # if xPositive: xRange = range(int(x0grid),int(x1grid))
        # else: xRange = range(int(x1grid),int(x0grid))
        if xPositive: step = 1
        else: step = -1
        for x in range(int(x0grid),int(x1grid),step):
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

def getElevationProfile(x0, y0, x1, y1):
    if type(x0)==str: x0 = float(x0)
    if type(y0)==str: y0 = float(y0)
    if type(x1)==str: x1 = float(x1)
    if type(y1)==str: y1 = float(y1)
    return gtopo.getElevationProfile(x0, y0, x1, y1)
