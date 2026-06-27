 #include "udf.h"
 #include "dpm.h"

 #define REMOVE_PARTICLES FALSE
 #define K_abs 0.3
 #define SIGMA_SB 5.67e-8
 #define K_emis 0.3

//int Pnum = 10;
real Qmax[] = {2834380000, 3831760000, 6737910000, 12138520000, 21282500000, 28922130000, 45974610000, 73750700000, 104547480000, 138876060000};
real K[] = {6980000, 5490000, 19860000, 13540000, 7290000, 4080000, 3550000, 1580000, 1360000, 1220000};
real Z[] = {0.027, 0.025, 0.023, 0.021, 0.019, 0.017, 0.015, 0.013, 0.012, 0.011};
real R[] = {0.000636, 0.000547, 0.000413, 0.000354, 0.000232, 0.000199, 0.000184, 0.00012, 0.000105, 0.000091};
real test_ns, test_v1, test_v2;
 
  real Qform(real Rf, real Qf, real Kf)
	{
	return Qf*exp(-Kf*Rf*Rf);
	}
 
 real Q(real rmy, real zmy)
{
	real Qprev, Qnext, Rloc;
	int i=0;
	if (zmy < 0.011) return 0;
	else if (zmy > 0.027) return 0;
	else{
		while (zmy<=Z[i+1]) {++i;}
		}
		Rloc = R[i]+((zmy-Z[i])*(R[i+1]-R[i])/(Z[i+1]-Z[i]));
		if (rmy>Rloc) return 0;
		else{
			Qprev = Qform(rmy, Qmax[i], K[i]);
			Qnext = Qform(rmy, Qmax[i+1], K[i+1]);
			return Qprev+((zmy-Z[i])*(Qnext-Qprev)/(Z[i+1]-Z[i]));
			}
}
  
DEFINE_ON_DEMAND(test_my_func)
 {
	 real Qtest;
	 Qtest = Q(0, 0.014);
	 Message("Q tested: %e\n", Qtest);
	 Message("values tested: %e %e %e\n", test_ns, test_v1, test_v2);
 }
 
 /*DEFINE_DPM_LAW(TemperatureLaw,p,ci)
{
cell_t c = P_CELL(p);
Thread *t = P_CELL_THREAD(p);

//P_T(p) += 2*K_abs*Q(P_POS(p)[1], P_POS(p)[0])*P_DT(p)/(P_RHO(p)*P_DIAM(p)*DPM_SPECIFIC_HEAT(p,P_T(p)));
//C_T(c,t) = P_T(p);
}*/

DEFINE_DPM_HEAT_MASS(multivap,p,Cp,hgas,hvap,cvap_surf,Z,dydt,dzdt)
 {
int ns;
   Material *sp;
   real dens_total = 0.0;     /* total vapor density*/
   real P_total = 0.0;      /* vapor pressure */
   int nc = TP_N_COMPONENTS(p);   /* number of particle components */
   
   test_ns = nc;
   
   Thread *t0 = P_CELL_THREAD(p);   /* thread where the particle is in*/
   Material *gas_mix = THREAD_MATERIAL(DPM_THREAD(t0, p)); /* gas mixture
   material */
   Material *cond_mix = P_MATERIAL(p); /* particle mixture material*/
   cphase_state_t *c = &(p->cphase); /* cell information of particle location*/
   real molwt[MAX_SPE_EQNS]; /* molecular weight of gas species */
   real Tp = P_T(p);   /* particle temperature */
   real mp = P_MASS(p);   /* particle mass */
   real molwt_bulk = 0.;  /* average molecular weight in bulk gas */
   real Dp = DPM_DIAM_FROM_VOL(mp / P_RHO(p)); /* particle diameter */
   real Ap = DPM_AREA(Dp);      /* particle surface */
   real Pr = c->sHeat * c->mu / c->tCond;   /* Prandtl number */
   real Nu = 2.0 + 0.6 * sqrt(p->Re) * pow(Pr, 1./3.); /* Nusselt number */
   real h = Nu * c->tCond / Dp;     /* Heat transfer coefficient*/
   real dh_dt = h * (c->temp - Tp) * Ap;  /*convective heat source term*/
   real dhrad_dt = K_emis*SIGMA_SB*(pow(Tp,4) - pow(c->temp,4)) * Ap;	/*radiative heat source term*/
   
   dydt[0] +=  2*K_abs*Q(P_POS(p)[1], P_POS(p)[0])/(P_RHO(p)*P_DIAM(p)*Cp) + dh_dt / (mp * Cp) - dhrad_dt / (mp * Cp);
   
   dzdt->energy -= dh_dt;
   mixture_species_loop(gas_mix,sp,ns)
   {
      molwt[ns] = MATERIAL_PROP(sp,PROP_mwi); /* molecular weight of gas
         species */
    molwt_bulk += c->yi[ns] / molwt[ns]; /* average molecular weight */
   }

 /* prevent division by zero */
 molwt_bulk = MAX(molwt_bulk,DPM_SMALL);

 for (ns = 0; ns < nc; ns++)
   {
      int gas_index = TP_COMPONENT_INDEX_I(p,ns);  /* gas species index of
       vaporization */
  if(gas_index >= 0)
    {
       /* condensed material */
       Material * cond_c = MIXTURE_COMPONENT(cond_mix, ns);
       /* vaporization temperature */
       real vap_temp = MATERIAL_PROP(cond_c,PROP_vap_temp);
       /* diffusion coefficient */
       real D = MATERIAL_PROP_POLYNOMIAL(cond_c, PROP_binary_diffusivity, c->temp);
       /* Schmidt number */
       real Sc = c->mu / (c->rho * D);
       /* mass transfer coefficient */
       real k = (2. + 0.6 * sqrt(p->Re) * pow(Sc, 1./3.)) * D / Dp;
       /* bulk gas concentration (ideal gas) */
       real cvap_bulk = c->pressure / UNIVERSAL_GAS_CONSTANT / c->temp
       * c->yi[gas_index] / molwt_bulk / solver_par.molWeight[gas_index];
       /* vaporization rate */
       real vap_rate = k * molwt[gas_index] * Ap
       * (cvap_surf[ns] - cvap_bulk);
       /* no vaporization below vaporization temperature, no condensation */
       if (Tp < vap_temp || vap_rate < 0.0)
         vap_rate = 0.;

       dydt[1+ns] -= vap_rate;   
       dzdt->species[gas_index] += vap_rate;
       /* dT/dt = dh/dt / (m Cp)*/
       dydt[0] -= hvap[gas_index] * vap_rate / (mp * Cp);
       /* gas enthalpy source term */
       dzdt->energy += hgas[gas_index] * vap_rate;

       P_total += cvap_surf[ns];
       dens_total += cvap_surf[ns] * molwt[gas_index];
      }
   }
   /* multicomponent boiling */
   P_total *= Z * UNIVERSAL_GAS_CONSTANT * Tp;
   
   test_v1=Z;
   test_v2=P_total;
   
   if (dydt[0] > 0){
        real h_boil = dydt[0] * mp * Cp;
        for (ns = 0; ns < nc; ns++)
          {
             int gas_index = TP_COMPONENT_INDEX_I(p,ns);
             if (gas_index >= 0)
               {
				/* condensed material */
				Material * cond_c = MIXTURE_COMPONENT(cond_mix, ns);
				/* boiling temperature */
				real boil_temp = DPM_BOILING_TEMPERATURE(p,cond_c);
				if (Tp>boil_temp){
				/* keep particle temperature constant */
				dydt[0] = 0.;
                  real boil_rate = h_boil / hvap[gas_index] * cvap_surf[ns] *
                     molwt[gas_index] / dens_total;
                  /* particle component mass source term */
                  dydt[1+ns] -= boil_rate;
                  /* fluid species source */
                  dzdt->species[gas_index] += boil_rate;
                  /* fluid energy source */
                  dzdt->energy += hgas[gas_index] * boil_rate;
				}
               }
          }
     }
 }

DEFINE_DPM_OUTPUT(discrete_phase_sample,header,fp,p,t,plane)
 {
    real y;
    if(header)
    {
     par_fprintf_head(fp," #Time[s]  R [m]  X-velocity[m/s]");
     par_fprintf_head(fp," W-velocity[m/s] R-velocity[m/s] ");
     par_fprintf_head(fp,"Drop Diameter[m] Number of Drops  ");
     par_fprintf_head(fp,"Temperature [K] Initial Diam [m] ");
     par_fprintf_head(fp,"Injection Time [s] \n");
    }
    if(NULLP(p))
      return;
      y = P_POS(p)[1];
   par_fprintf(fp,"%d %" int64_fmt " %e %f %f %f %f %e %e %f %e %f \n",
  P_INJ_ID(P_INJECTION(p)),p->part_id, P_TIME(p),y,P_VEL(p)[0],
  P_VEL(p)[1],P_VEL(p)[2],P_DIAM(p),P_N(p),  
  P_T(p), P_INIT_DIAM(p),p->time_of_birth);
 
 
   #if REMOVE_PARTICLES
      MARK_PARTICLE(p, P_FL_REMOVED);
   #endif
 } 