import { Injectable } from '@angular/core';
import { Apollo, QueryRef } from 'apollo-angular';
import gql from 'graphql-tag';



@Injectable()
export class PoolService  {

    constructor(private service: Apollo) {}

    public getPool(id:number): QueryRef<any,any> {
        return this.service.watchQuery<any>({
            query: gql`  
                        query getPool($id: Int!) {
                            pool(id: $id) {
                                name,
                                state {
                                    available {
                                        info
                                    }
                                }
                            }
                        }
            `,
            variables: {
                method: 'GET',
                id: id
            }
        })
    }

}
