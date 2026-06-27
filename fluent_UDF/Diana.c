#include "udf.h"

define x0 0.05
define y0 0.05
define z0 0.05
define x1 0.05
define y1 0.05
define z1 0.05


real R[] = {-0.0019, -0.0017, -0.0015, -0.0013, -0.0011, -0.0009, -0.0007, -0.0005, -0.0003, -0.0001, 0.0001, 0.0003, 0.0005, 0.0007, 0.0009, 0.0011, 0.0013, 0.0015, 0.0017, 0.0019};
real Vrad[]
real Vax[]
real Vtan[]


/*LINEAR INTERPOLATION UNIVERSAL FUNCTION*/
 real LInterp (real rmy, real FInt[])
 {
 int i=0;
 if (rmy>=R_TEST) return 0;
 else
	{
	while(rmy>=R[i+1])
		{i++;}
	return FInt[i]+((rmy-R[i])*(FInt[i+1]-FInt[i])/(R[i+1]-R[i]));
	}
}
  




DEFINE_PROFILE(inlet_Vx, thread, position)
{

  real x[ND_ND]; /* this will hold the position vector */  
  real x, z;
  face_t f;
 
  x0 = 5;

  begin_f_loop(f,thread)
  {
    F_CENTROID(x, f, thread);
    x = x[0];
    y = x[1];
    z = x[2];
    F_PROFILE(f, thread, position) = LInterp(R_my, Vax);
  }
  end_f_loop(f, thread)

DEFINE_PROFILE(inlet_Vy, thread, position)
{
}

DEFINE_PROFILE(inlet_Vz, thread, position)
{
}

}