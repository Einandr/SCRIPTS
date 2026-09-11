#include "udf.h"

#define STOICH_COEFF 4.0 

DEFINE_SOURCE(fuel_disappearance_source, c, t, dS, eqn)
{
    real dt = CURRENT_TIME_STEP;
    real rho = C_R(c,t);
    
    /* Получаем текущие массовые доли компонентов в ячейке */
    real y_fuel = C_YI(c,t,0); /* 0 - индекс топлива в списке Species */
    real y_ox   = C_YI(c,t,1); /* 1 - индекс окислителя */
    
    real source;
    real max_fuel_burnt_by_ox = (y_ox / STOICH_COEFF) * rho / dt;
    real max_fuel_burnt_by_fuel = y_fuel * rho / dt;
    
    /* Скорость реакции лимитируется тем компонентом, которого меньше */
    if (max_fuel_burnt_by_fuel < max_fuel_burnt_by_ox)
    {
        source = -max_fuel_burnt_by_fuel;
        dS[eqn] = -rho / dt; /* Производная для численной стабилизации */
    }
    else
    {
        source = -max_fuel_burnt_by_ox;
        dS[eqn] = 0.0;
    }
    
    return source; /* Возвращает отрицательный источник (убыль) топлива в кг/(м3*с) */
}
