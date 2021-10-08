import { IPoolDetail } from '../pools.service';

export interface IPoolDetailClient {
    farmList: any[]
    host: string
    password: string
    permissions: string[]
    poolType: string
    port: number
    vmControllerAddress: string
    vmId: string
    vmVerboseName: string
    token: string
  }
  
export class PoolDetailMapper {
  public static transformToClient(poolDetail: IPoolDetail): IPoolDetailClient {
    const { farm_list, host, password, permissions, pool_type, vm_controller_address, vm_id, port, vm_verbose_name, token } = poolDetail;
    return {
        vmControllerAddress: vm_controller_address,
        vmId: vm_id,
        poolType: pool_type,
        farmList: farm_list,
        vmVerboseName: vm_verbose_name,
        host,
        password,
        permissions,
        port,
        token
    }
  }

}
