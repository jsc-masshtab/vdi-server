import { IParams } from './../../../../types/index.d';
import { WaitService } from './../../common/components/single/wait/wait.service';
import { Injectable } from '@angular/core';
import { Apollo } from 'apollo-angular';
import gql from 'graphql-tag';
import { timer, Observable } from 'rxjs';
import { switchMap, map } from 'rxjs/operators';



/**
 * вызов метода при: 1) onInit() spin:true по умолчанию
 *                   2) sort spin:true,nameSort:new,reverse:new
 *                   3) обновление при: создании/удаление пула, добавление/удаление юзера, добавление/удаление вм у стат.пула
 *                           spin:false,nameSort:old,reverse:old
 *                   4) при refresh spin:false,nameSort:old,reverse:old
 */

@Injectable()
export class PoolsService {

    public paramsForGetPools: IParams = { // для несбрасывания параметров сортировки при всех обновлениях
        spin: true,
        nameSort: undefined
    };

    constructor(private service: Apollo, private waitService: WaitService) { }

    public getAllPools(obs?: {obs: boolean}): Observable<any> {

        if (this.paramsForGetPools.spin) {
            this.waitService.setWait(true);
        }

        if (obs && obs.obs) {
            var obs$ = timer(0, 60000);

            obs$ = timer(0, 60000);
            return obs$.pipe(switchMap(() => {
                return this.service.watchQuery({
                    query: gql` query pools($ordering:String) {
                                    pools(ordering: $ordering) {
                                        pool_id
                                        verbose_name
                                        vms {
                                            id
                                        }
                                        pool_type
                                        controller {
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
                        ordering: this.paramsForGetPools.nameSort
                    }
                }).valueChanges.pipe(map(data => data.data['pools']));
            }));
        } else {
            return this.service.watchQuery({
                query: gql` query pools($ordering:String) {
                                pools(ordering: $ordering) {
                                    pool_id
                                    verbose_name
                                    vms {
                                        id
                                    }
                                    pool_type
                                    controller {
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
                    ordering: this.paramsForGetPools.nameSort
                }
            }).valueChanges.pipe(map(data => data.data['pools']));
        }
    }
}
