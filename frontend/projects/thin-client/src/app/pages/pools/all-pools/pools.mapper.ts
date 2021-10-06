import { IPool } from '../pools.service';

export interface IPoolClient {
    connectionTypes: string[]
    id: string
    name: string
    osType: null | string
    status: string
  }
  
export class PoolMapper {
  public static transformToClient(pool: IPool): IPoolClient {
    const { connection_types, os_type, id, name, status } = pool;
    return {
        connectionTypes: connection_types,
        osType: os_type,
        id,
        name,
        status
    }
  }

}
