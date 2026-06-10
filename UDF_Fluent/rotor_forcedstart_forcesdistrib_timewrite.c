#include "udf.h"
#include "dynamesh_tools.h"
#include "sg.h"
#include <stdio.h>
#include <stdlib.h>
#include <crtdbg.h>
#include <string.h>
#include <time.h>


# define time_turn_off 0.5
# define moment_start 10000.0

int write_frequency = 10;
int w_id[] = {23,24,25};
char w_name[][50] = {"w_b1", "w_b2", "w_c"};



 char* concat(const char *s1, const char *s2, const char *s3, const char *s4, const char *s5)
{	char *result = malloc(strlen(s1)+strlen(s2)+strlen(s3)+strlen(s4)+strlen(s5)+1);
	strcpy(result, s1);
	strcat(result, s2);
	strcat(result, s3);
	strcat(result, s4);
	strcat(result, s5);
	return result;
}


real **allocate_2D_array(int size1, int size2)
{
    real** array_2d = (real**)malloc(size1 * sizeof(real*));
    for (int i=0; i<size1; i++)
        array_2d[i] = (real*)malloc(size2 * sizeof(real));
    return array_2d;
}


real **concat_2d_arr(real **A, real **B, int size_A, int size_B, int size2)
{
    int size_C = size_A + size_B;
    real **C = (real**)malloc((size_C+1) * sizeof(real*));
    for (int i=0; i<size_C; i++)
       C[i] = (real*)malloc(size2 * sizeof(real));
   
    for (int i=0; i<(size_A); i++)
        memcpy(C[i], A[i], size2*sizeof(real*));
    for (int i=0; i<(size_B); i++)
        memcpy(C[size_A+i], B[i], size2*sizeof(real*));

   return C;
}


void free_2d_array(real** array_2d, int size1)
{
    for (int i=0; i<size1; i++)
        free(array_2d[i]);
    free(array_2d);
}


DEFINE_SDOF_PROPERTIES(rotor, prop, dt, time, dtime)
{
	prop[SDOF_MASS] = 1.0;
	prop[SDOF_IXX] = 1.0;
	prop[SDOF_IYY] = 1.0;
	prop[SDOF_IZZ] = 1.0;
	prop[SDOF_ZERO_TRANS_X] = True;
	prop[SDOF_ZERO_TRANS_Y] = True;
	prop[SDOF_ZERO_TRANS_Z] = True;
	prop[SDOF_ZERO_ROT_X] = True;
	prop[SDOF_ZERO_ROT_Y] = False;
	prop[SDOF_ZERO_ROT_Z] = True;
	if (time < time_turn_off){
		prop[SDOF_LOAD_M_Y] = moment_start;}
	else{
		prop[SDOF_LOAD_M_Y] = 0;}	
	#if RP_HOST
		printf("\nrotor: updating sdof properties");
	#endif
}


 void write_on_surface(int zone_ID, char *zone_name)
{
real (*array_x)[ND_ND], (*array_a)[ND_ND], (*array_fv)[ND_ND];
real *array_p;
int n_faces, n_faces_total, pe;


#if !RP_NODE
	real time;
	time = CURRENT_TIME;
	char time_string[sizeof(real)*8];
	sprintf(time_string, "%g", time);

	int i, j;
	FILE *fp;
	char* name_file = concat("parameters_", zone_name, "_", time_string,  ".txt");
	fp = fopen(name_file, "w");
	free(name_file);
	fprintf(fp, "%s", "x y z ax ay az p fvx fvy fvz\n");
#endif


#if !RP_HOST	
	Domain *d;
    d = Get_Domain(1);
    Thread *t = Lookup_Thread(d, zone_ID);
    face_t f;
	n_faces = THREAD_N_ELEMENTS_INT(t);
	int i, j;
	
	array_p = (real *)malloc(n_faces * sizeof(real));
	array_x=(real (*)[ND_ND])malloc(ND_ND*n_faces*sizeof(real));
	array_a=(real (*)[ND_ND])malloc(ND_ND*n_faces*sizeof(real));
	array_fv=(real (*)[ND_ND])malloc(ND_ND*n_faces*sizeof(real));
	
	begin_f_loop(f,t)
		{
		array_p[f] = F_P(f,t);
		F_CENTROID(array_x[f],f,t);
		F_AREA(array_a[f],f,t);
		memcpy(array_fv[f], F_STORAGE_R_N3V(f,t,SV_WALL_SHEAR), ND_ND*sizeof(real));
		}
	end_f_loop(f,t)

	pe = (I_AM_NODE_ZERO_P) ? node_host : node_zero;
	PRF_CSEND_INT(pe, &n_faces, 1, myid);
	PRF_CSEND_REAL(pe, array_p, n_faces, myid);
	PRF_CSEND_REAL(pe, array_x[0], n_faces*ND_ND, myid);
	PRF_CSEND_REAL(pe, array_a[0], n_faces*ND_ND, myid);
	PRF_CSEND_REAL(pe, array_fv[0], n_faces*ND_ND, myid);
	free(array_p);
	free(array_x);
	free(array_a);
	free(array_fv);

	
	if (I_AM_NODE_ZERO_P)
		{
		compute_node_loop_not_zero (i)
			{
			PRF_CRECV_INT(i, &n_faces, 1, i);
			array_p = (real *)malloc(n_faces * sizeof(real));
			array_x=(real(*)[ND_ND])malloc(ND_ND*n_faces*sizeof(real));
			array_a=(real(*)[ND_ND])malloc(ND_ND*n_faces*sizeof(real));
			array_fv=(real(*)[ND_ND])malloc(ND_ND*n_faces*sizeof(real));
			PRF_CRECV_REAL(i, array_p, n_faces, i);
			PRF_CRECV_REAL(i, array_x[0], ND_ND*n_faces, i);
			PRF_CRECV_REAL(i, array_a[0], ND_ND*n_faces, i);
			PRF_CRECV_REAL(i, array_fv[0], ND_ND*n_faces, i);
			PRF_CSEND_INT(node_host, &n_faces, 1, myid);
			PRF_CSEND_REAL(node_host, array_p, n_faces, myid);
			PRF_CSEND_REAL(node_host, array_x[0], ND_ND*n_faces, myid);
			PRF_CSEND_REAL(node_host, array_a[0], ND_ND*n_faces, myid);
			PRF_CSEND_REAL(node_host, array_fv[0], ND_ND*n_faces, myid);
			free((char *)array_p);
			free((char *)array_x[0]);
			free((char *)array_a[0]);
			free((char *)array_fv[0]);
			}
		}
		
	n_faces_total = PRF_GISUM1(n_faces);	
#endif


#if RP_HOST
//fprintf(fp, "%i", n_faces_total);


	compute_node_loop(i)
	{
		PRF_CRECV_INT(node_zero, &n_faces, 1, node_zero);
		array_p = (real *)malloc(n_faces*sizeof(real));
		array_x = (real (*)[ND_ND])malloc(ND_ND*n_faces*sizeof(real));
		array_a = (real (*)[ND_ND])malloc(ND_ND*n_faces*sizeof(real));
		array_fv = (real (*)[ND_ND])malloc(ND_ND*n_faces*sizeof(real));
		PRF_CRECV_REAL(node_zero, array_p, n_faces, node_zero);
		PRF_CRECV_REAL(node_zero, array_x[0], ND_ND*n_faces, node_zero);
		PRF_CRECV_REAL(node_zero, array_a[0], ND_ND*n_faces, node_zero);
		PRF_CRECV_REAL(node_zero, array_fv[0], ND_ND*n_faces, node_zero);
		
		for (j=0; j<n_faces; j++)
			fprintf(fp, "%e %e %e %e %e %e %e %e %e %e\n", array_x[j][0], array_x[j][1], array_x[j][2], array_a[j][0], array_a[j][1], array_a[j][2], array_p[j], array_fv[j][0], array_fv[j][1], array_fv[j][2]);
		free(array_p);
		free(array_x);
		free(array_a);
		free(array_fv);
	}

fclose(fp);
#endif

}


DEFINE_ON_DEMAND(on_demand_calc)
{
//write_on_surface(240, "w_s");
//write_on_surface(wall_id[2], wall_name[2]);
for (int i=0; i<sizeof(w_id)/sizeof(int); i++)
	write_on_surface(w_id[i], w_name[i]);
}


DEFINE_EXECUTE_AT_END(execute_at_end)
{

//Domain *d;
//d = Get_Domain(1);
int n_time;
n_time = N_TIME;

Message0("time step is: %i\n", n_time);

if (n_time % write_frequency == 0)
	{
	Message0("time step is from cycle: %i\n", n_time);
	for (int i=0; i<sizeof(w_id)/sizeof(int); i++)
		write_on_surface(w_id[i], w_name[i]);
	}

}

