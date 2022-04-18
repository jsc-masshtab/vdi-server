import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { IParams } from '@app/shared/types';
import { environment } from 'environments/environment';
import { IResponse } from '../../interfaces/https';



export interface IPool {
  connection_types: string[]
  id: string
  name: string
  os_type: null | string
  status: string
}

export interface IPoolDetail {
  farm_list: any[]
  host: string
  password: string
  permissions: string[]
  pool_type: string
  port: number
  vm_controller_address: string
  vm_id: string
  vm_verbose_name: string
  token: string
}


export enum VMActions {
  Start = 'start',
  Suspend = 'suspend',
  Shutdown = 'shutdown',
  ForceShutdown = 'force_shutdown',
  Reboot = 'reboot',
  ForceReboot = 'force_reboot'
}



@Injectable({
  providedIn: 'root'
})
export class PoolsService {
  private url = `${environment.api}client/pools`;


  public paramsForGetPools: IParams = { // для несбрасывания параметров сортировки при всех обновлениях
    spin: true,
    nameSort: undefined
};
  constructor(private http: HttpClient ) {
   }

   public getPools(): Observable<IResponse<IPool[]>> {
      return this.http.get<IResponse<IPool[]>>(this.url);
   }

   public getPoolDetail(id: string): Observable<IResponse<IPoolDetail>> {
      return this.http.post<IResponse<IPoolDetail>>(`${this.url}/${id}/`, {});
   }

   public manageVM( body: {id: string, action: VMActions, force?: boolean} ): Observable<IResponse<string>> {
    return this.http.post<IResponse<string>>(`${this.url}/${body.id}/${body.action}/`, body.force ? {force: true} : {});
   }
}
