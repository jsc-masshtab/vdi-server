import { IParams } from '../../../../../../types';
import {Injectable} from '@angular/core';
import { Apollo, QueryRef } from 'apollo-angular';
import gql from 'graphql-tag';


@Injectable()
export class DatapoolsService {

    public paramsForGetDatapools: IParams = { // для несбрасывания параметров сортировки при всех обновлениях
        spin: true,
        nameSort: undefined
    };

    constructor(private service: Apollo) {}

    public getAllDatapools(): QueryRef<any, any> {
        return  this.service.watchQuery({
            query:  gql` query resources($ordering:String) {
                            datapools(ordering: $ordering) {
                                id
                                used_space
                                free_space
                                status
                                type
                                verbose_name
                                controller {
                                    id
                                    verbose_name
                                }
                            }
                        }
                    `,
            variables: {
                method: 'GET',
                ordering: this.paramsForGetDatapools.nameSort
            }
        });
    }

    public getDatapool(id: string, controller_address: string): QueryRef<any, any> {
        return  this.service.watchQuery({
            query: gql` query resources($id: UUID, $controller_address: UUID) {
                            datapool(datapool_id: $id, controller_id: $controller_address) {
                                used_space
                                free_space
                                size
                                status
                                type
                                verbose_name
                            }
                        }
                    `,
            variables: {
                method: 'GET',
                id,
                controller_address
            }
        });
    }
}


