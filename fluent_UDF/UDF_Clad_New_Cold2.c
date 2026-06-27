 #include "udf.h"
 #include "dynamesh_tools.h"
 
 #define R_TEST 0.0019
 #define T_melt 1500
 #define V 0.005
 #define X0 0
 #define Y0 0
 #define RO_Ni 8900
  
 #define NUM_UDM 1 
 static int udm_offset = UDM_UNRESERVED;
 #define COLD_CHECK(f,t) f_UDMI(f,t,udm_offset)
  
real R[] = {-0.0019, -0.0017, -0.0015, -0.0013, -0.0011, -0.0009, -0.0007, -0.0005, -0.0003, -0.0001, 0.0001, 0.0003, 0.0005, 0.0007, 0.0009, 0.0011, 0.0013, 0.0015, 0.0017, 0.0019};

real SHeat[] = {811243.378062313, 1343401.31242347, 1943587.03680877, 2558643.15262042, 3290467.27044324, 3942659.71506485, 4882364.4740506, 11242290.4981363, 26784267.4759261, 46455130.1020812, 46455130.1020812, 26784267.4759261, 11242290.4981363, 4882364.4740506, 3942659.71506485, 3290467.27044324, 2558643.15262042, 1943587.03680877, 1343401.31242347, 811243.378062313};

real SMass[] = {0.724368033257577, 1.23853491673684, 1.62122182321289, 1.84716638887281, 2.3628254228824, 2.38594849349915, 1.42302629928832, 6.36838918641466, 22.699472569274, 44.2014943840637, 44.2014943840637, 22.699472569274, 6.36838918641464, 1.42302629928832, 2.38594849349915, 2.3628254228824, 1.84716638887281, 1.62122182321289, 1.23853491673684, 0.724368033257577};
 
 real SMass_Cold[] = {0, 0, 0.777837653313594, 4.88160757657846, 11.3057734591335, 18.3123446451651, 23.1308298643404, 21.6125385286727, 11.5796574671502, 0, 0, 11.5796574671502, 21.6125385286727, 23.1308298643404, 18.3123446451651, 11.3057734591335, 4.88160757657845, 0.777837653313592, 0, 0};
 
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
  
  real SH(real rmy)
{
	return LInterp(rmy, SHeat);
}

  real SM(real rmy)
{
	return LInterp(rmy, SMass);
}

  real SM_Cold(real rmy)
{
	return LInterp(rmy, SMass_Cold);
}

  real SH_Beam(real rmy)
 {
	real Rloc;
	if (fabs(rmy)<=0.000636)
		return 2834380000*exp(-6980000*rmy*rmy);
	else return 0;
}


#if !RP_HOST
  int SM_Cold_Check(Dynamic_Thread *dt, real x_def[ND_ND])
 {
	Domain *domain;
	Thread *t;
	real x[ND_ND];
	real distance, distance_min = 1000;
	int tid, fmin;
	face_t f;
	
	domain = THREAD_DOMAIN (DT_THREAD (dt));
	tid = THREAD_ID (DT_THREAD (dt));
	t = Lookup_Thread (domain, tid);
	
	//int thread_id = 9; //THIS IS THREAD ID TO BE CHANGED
	/*domain = Get_Domain(1);	
	Thread *t = Lookup_Thread(domain, thread_id);*/
	
	
	
	begin_f_loop(f,t)
	{
	F_CENTROID(x,f,t);
	distance = sqrt(pow((x_def[0]-x[0]),2)+pow((x_def[1]-x[1]),2)+pow((x_def[2]-x[2]),2));
	if (distance < distance_min)
		{
		distance_min=distance;
		fmin=f;
		}
	}
	end_f_loop(f,t)
	
	/*begin_f_loop(f,t)
		{
		if (F_T(f,t) >= T_melt)
		COLD_CHECK(f,t) = 1.0;
		else COLD_CHECK(f,t) = 0.0;
		}
	end_f_loop(f,t)*/

	if (F_T(fmin,t) >= T_melt)
	return 1;
	else return 0;
 } 
#endif


DEFINE_ON_DEMAND(test_my_func)
 {
	real VT1, VT2, VT3, VT4;
	/*	
	#if !RP_HOST
	real PTest[3]={0.0002,0,0.00025};
	VT2 = SM_Cold_Check(PTest);
	Message("Test before summing: %e\n", VT2);
	#endif
	
	# if RP_NODE
	VT2 = PRF_GIHIGH1(VT2);
	#endif
	
	node_to_host_real_1(VT2);
	
	#if !RP_NODE
	VT1 = SM_Cold(0.0012);
	Message("Test: %e %e\n", VT1, VT2);
	#endif*/
 }
 
 
  DEFINE_EXECUTE_ON_LOADING(on_loading, libudf)
 {
    if (udm_offset == UDM_UNRESERVED) udm_offset = Reserve_User_Memory_Vars(NUM_UDM);
    if (udm_offset == UDM_UNRESERVED)
     Message("\nYou need to define up to %d extra UDMs in GUI and then reload current library %s\n", NUM_UDM, libudf);
    else
     {
      Message("%d UDMs have been reserved by the current library %s\n", NUM_UDM, libudf);
      Set_User_Memory_Name(udm_offset,"lib1-UDM-0");
     }
    Message("\nUDM Offset for Current Loaded Library = %d",udm_offset);
 }
 
 
DEFINE_PROFILE(WHeat,t,i)
{
    face_t f;
	real x[ND_ND];
	real Y, X, RLoc, S;
	X=X0+V*CURRENT_TIME;
	Y=Y0;
    begin_f_loop(f,t)
		{
		F_CENTROID(x,f,t);
			RLoc = sqrt(pow((x[0]-X),2)+pow((x[1]-Y),2));
			if (RLoc>=R_TEST){S=0;}
			else{
			S = SH(RLoc)+SH_Beam(RLoc);}
			F_PROFILE(f,t,i) = S;
		}
    end_f_loop(f,t)
 }

DEFINE_GEOM(parabola,domain,dt,position)
 {
	#if !RP_HOST	 
	real X, Y, RLoc, dtime;
	real PTest2[3];
	
	PTest2[0]=position[0];
	PTest2[1]=position[1];
	PTest2[2]=position[2];
	int ColdCheck=0;
	
	X=X0+V*CURRENT_TIME;
	Y=Y0;
	RLoc=sqrt(pow((position[0]-X),2) + pow((position[1]-Y),2));
	dtime=CURRENT_TIMESTEP;
		if (RLoc <= R_TEST)
			{
			ColdCheck = SM_Cold_Check(dt, PTest2);
			Message("DynamicTest: %i\n", ColdCheck);
			position[2] += SM_Cold(RLoc)*dtime/RO_Ni*ColdCheck + SM(RLoc)*dtime/RO_Ni;
			}
	#endif
}