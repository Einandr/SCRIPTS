#include "udf.h"
#include "sg.h"
#include <stdlib.h>
#include <string.h>

 char* concat(const char *s1, const char *s2, const char *s3)
{	char *result = malloc(strlen(s1)+strlen(s2)+strlen(s3)+1);
	strcpy(result, s1);
	strcat(result, s2);
	strcat(result, s3);
	return result;
}

 void write_on_surface(int zone_ID, const char *zone_name)
{
#if !RP_HOST	
    real x[ND_ND], A[ND_ND], es[ND_ND], dr0[ND_ND], ds, A_by_es;
    Domain *d;
    d = Get_Domain(1);
    Thread *t = Lookup_Thread(d, zone_ID);
    face_t f;
#else
	int i;
#endif

#if !RP_NODE
	FILE *fp;
	char* name_file = concat("parameters_", zone_name, ".txt");
	fp = fopen(name_file, "w");
	free(name_file);
	fprintf(fp, "%s", "x y z H A T\n");
#endif

#if PARALLEL
	int size, size_host;
	real *array_x1, *array_x2, *array_x3, *array_fhf, *array_At, *array_T;
	int pe;
#endif


#if RP_NODE

	size = 0;
	begin_f_loop(f,t)
	if PRINCIPAL_FACE_P(f,t)
	{
		size+=1;
	}
	end_f_loop(f,t)
	
	array_x1 = (real *)malloc(size * sizeof(real));
	array_x2 = (real *)malloc(size * sizeof(real));
	array_x3 = (real *)malloc(size * sizeof(real));
	array_fhf = (real *)malloc(size * sizeof(real));
	array_At = (real *)malloc(size * sizeof(real));
	array_T = (real *)malloc(size * sizeof(real));
	
	
	begin_f_loop(f,t)
	if PRINCIPAL_FACE_P(f,t)
	{
		F_CENTROID(x,f,t);
		array_x1[f] = x[0];
		array_x2[f] = x[1];
		array_x3[f] = x[2];
		array_fhf[f] = BOUNDARY_HEAT_FLUX(f,t);
		BOUNDARY_FACE_GEOMETRY(f,t,A,ds,es,A_by_es,dr0);
		array_At[f] = NV_MAG(A);
		array_T[f] = F_T(f,t);
	}
	end_f_loop(f,t)

	pe = (I_AM_NODE_ZERO_P) ? node_host : node_zero;
    PRF_CSEND_INT(pe, &size, 1, myid);
    PRF_CSEND_REAL(pe, array_x1, size, myid);
	PRF_CSEND_REAL(pe, array_x2, size, myid);
	PRF_CSEND_REAL(pe, array_x3, size, myid);
	PRF_CSEND_REAL(pe, array_fhf, size, myid);
	PRF_CSEND_REAL(pe, array_At, size, myid);
	PRF_CSEND_REAL(pe, array_T, size, myid);
	free(array_x1);
	free(array_x2);
	free(array_x3);
	free(array_fhf);
	free(array_At);
	free(array_T);
	

if (I_AM_NODE_ZERO_P)
	compute_node_loop_not_zero (pe)
	{
		PRF_CRECV_INT(pe, &size, 1, pe);
        array_x1 = (real *)malloc(size * sizeof(real));
		array_x2 = (real *)malloc(size * sizeof(real));
		array_x3 = (real *)malloc(size * sizeof(real));
		array_fhf = (real *)malloc(size * sizeof(real));
		array_At = (real *)malloc(size * sizeof(real));
		array_T = (real *)malloc(size * sizeof(real));
        PRF_CRECV_REAL(pe, array_x1, size, pe);
		PRF_CRECV_REAL(pe, array_x2, size, pe);
		PRF_CRECV_REAL(pe, array_x3, size, pe);
		PRF_CRECV_REAL(pe, array_fhf, size, pe);
		PRF_CRECV_REAL(pe, array_At, size, pe);
		PRF_CRECV_REAL(pe, array_T, size, pe);
        PRF_CSEND_INT(node_host, &size, 1, myid);
        PRF_CSEND_REAL(node_host, array_x1, size, myid);
		PRF_CSEND_REAL(node_host, array_x2, size, myid);
		PRF_CSEND_REAL(node_host, array_x3, size, myid);
		PRF_CSEND_REAL(node_host, array_fhf, size, myid);
		PRF_CSEND_REAL(node_host, array_At, size, myid);
		PRF_CSEND_REAL(node_host, array_T, size, myid);
        free((char *)array_x1);
		free((char *)array_x2);
		free((char *)array_x3);
		free((char *)array_fhf);
		free((char *)array_At);
		free((char *)array_T);
    }

#endif
	

#if RP_HOST
    compute_node_loop (pe)
    {
        PRF_CRECV_INT(node_zero, &size, 1, node_zero);
        array_x1 = (real *)malloc(size * sizeof(real));
		array_x2 = (real *)malloc(size * sizeof(real));
		array_x3 = (real *)malloc(size * sizeof(real));
		array_fhf = (real *)malloc(size * sizeof(real));
		array_At = (real *)malloc(size * sizeof(real));
		array_T = (real *)malloc(size * sizeof(real));
        PRF_CRECV_REAL(node_zero, array_x1, size, node_zero);
		PRF_CRECV_REAL(node_zero, array_x2, size, node_zero); 
		PRF_CRECV_REAL(node_zero, array_x3, size, node_zero); 
		PRF_CRECV_REAL(node_zero, array_fhf, size, node_zero); 
		PRF_CRECV_REAL(node_zero, array_At, size, node_zero); 
		PRF_CRECV_REAL(node_zero, array_T, size, node_zero); 		
    for (i=0; i<size; i++)
   		fprintf(fp, "%e %e %e %e %e %e\n", array_x1[i], array_x2[i], array_x3[i], array_fhf[i], array_At[i], array_T[i]);
    free(array_x1);
	free(array_x2);
	free(array_x3);
	free(array_fhf);
	free(array_At);
	free(array_T);
	
	}
#endif

#if !RP_NODE
    fclose(fp);
#endif
}


 void write_on_solid(int zone_ID, const char *zone_name)
{
    real x[ND_ND], x1, x2, x3, V, ct;
    Domain *d;
    d = Get_Domain(1);
    Thread *t = Lookup_Thread(d, zone_ID);
    cell_t c;
	FILE *fp;
	char* name_file = concat("parameters_", zone_name, ".txt");
	fp = fopen(name_file, "w");
	fprintf(fp, "%s", "x y z V T\n");

	begin_c_loop(c,t)
	{
	C_CENTROID(x,c,t);
	x1 = x[0];
	x2 = x[1];
	x3 = x[2];
    V = C_VOLUME(c,t);
	ct = C_T(c,t);
	fprintf(fp, "%e %e %e %e %e\n", x1, x2, x3, V, ct);
    }
	end_c_loop(c,t)
	fclose(fp);	
	free(name_file);
}
  
 
DEFINE_ON_DEMAND(on_demand_calc)
{
	
write_on_surface(4, "wall_tubeside");
//write_on_surface(5, "wall_shellside");
//write_on_solid(9, "fluid_shellside");
//write_on_solid(8, "fluid_tubeside");
}


