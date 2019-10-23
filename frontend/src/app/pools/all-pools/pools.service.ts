import { Injectable } from '@angular/core';
import { Apollo } from 'apollo-angular';
import gql from 'graphql-tag';
import { timer, Observable } from 'rxjs';
import { switchMap, map } from 'rxjs/operators';


interface IParams {
    spin: boolean;
    nameSort?: string | undefined;
    reverse?: boolean | undefined;
}


@Injectable()
export class PoolsService {

    public paramsForGetPools: IParams = {
        spin: true,
        nameSort: undefined,
        reverse: undefined
    };

    constructor(private service: Apollo) { }

    public getAllPools(param: IParams): Observable<any> {

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
                    ordering: param.nameSort,
                    reversed_order: param.reverse
                }
            }).valueChanges.pipe(map(data => data.data['pools']));
        }));
    }
}
