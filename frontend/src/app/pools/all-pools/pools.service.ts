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
        nameSort: undefined,
        reverse: undefined
    };

    constructor(private service: Apollo, private waitService: WaitService) { }

    public getAllPools(): Observable<any> {

        if (this.paramsForGetPools.spin) {
            this.waitService.setWait(true);
        }

        let obs$ = timer(0, 60000);
        return obs$.pipe(switchMap(() => {
            return this.service.watchQuery({
                query: gql` query allPools($ordering:String, $reversed_order: Boolean) {
                                pools(ordering: $ordering, reversed_order: $reversed_order) {
                                    id
                                    name
                                    vms {
                                        id
                                    }
                                    desktop_pool_type
                                    controller {
                                        ip
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
                    reversed_order: this.paramsForGetPools.reverse
                }
            }).valueChanges.pipe(map(data => data.data['pools']));
        }));
    }
}
