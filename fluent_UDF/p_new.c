#include "udf.h"

DEFINE_PROFILE(p_in, t, i)
{
  face_t f;
  real T = CURRENT_TIME;
  begin_f_loop(f,t)
  {
  if (T<=0.5)
  F_PROFILE(f,t,i) = 200000;
 else if (T>=6.5)
 F_PROFILE(f, t, i) = 4000000;
 else   F_PROFILE(f, t, i) = 633300.0*T-116700.0;
  }
  end_f_loop(f, t)
}