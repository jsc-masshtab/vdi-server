import { Injectable } from '@angular/core';
import { Apollo, QueryRef } from 'apollo-angular';
import gql from 'graphql-tag';

import { IParams } from '@shared/types';

/**
 * вызов метода при: 1) onInit() spin:true
 *                   2) sort spin:true,nameSort:new
 *                   3) обновление при: создании/удаление пула, добавление/удаление юзера пула и вм, добавление/удаление вм у стат.пула
 *                           spin:false,nameSort:old
 *                   4) при refresh spin:true,nameSort:old
 */

@Injectable()
export class PoolsService {

    public paramsForGetPools: IParams = { // для несбрасывания параметров сортировки при всех обновлениях
        spin: true,
        nameSort: undefined
    };

    constructor(private service: Apollo) { }

    public getAllControllers(): QueryRef<any, any> {
        return this.service.watchQuery({
            query: gql`
                query controllers {
                    controllers {
                        id
                    }
                }
            `,
            variables: {
                method: 'GET'
            }
        });
    }

    public getAllPools(props): QueryRef<any, any> {
        return this.service.watchQuery({
            query: gql` 
                query pools(
                    $ordering:ShortString,
                    $limit: Int,
                    $offset: Int
                ){
                    pools(
                        limit: $limit,
                        offset: $offset,
                        ordering: $ordering
                    ){
                        pool_id
                        verbose_name
                        vm_amount
                        pool_type
                        controller {
                            verbose_name
                            address
                        }
                        users {
                            username
                        }
                        status
                    }
                }
            `,
            variables: {
                method: 'GET',
                ordering: this.paramsForGetPools.nameSort,
                ...props
            }
        });
    }
}

