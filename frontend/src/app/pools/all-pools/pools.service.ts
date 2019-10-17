import { Injectable } from '@angular/core';
import { Apollo } from 'apollo-angular';
import gql from 'graphql-tag';
import { timer, Observable } from 'rxjs';
import { switchMap, map } from 'rxjs/operators';


@Injectable()
export class PoolsService {

    constructor(private service: Apollo) { }

    public getAllPools(obs?: boolean): Observable<any> {
        const obs$ = timer(0, 60000);

        if (obs) {
            return obs$.pipe(switchMap(() => {
                return this.service.watchQuery({
                    query: gql` query allPools {
                                    pools {
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
                        method: 'GET'
                    }
                }).valueChanges.pipe(map(data => data.data['pools']));
            }));
        } else {
            return this.service.watchQuery({
                query: gql` query allPools {
                                    pools {
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
                    method: 'GET'
                }
            }).valueChanges.pipe(map(data => data.data['pools']));
        }
    }
}
