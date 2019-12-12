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
                                vdisk_count
                                file_count
                                iso_count
                                verbose_name
                                controller {
                                    address
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
            query:  gql` query resources($id: String, $controller_address: String) {
                            datapool(id: $id, controller_address: $controller_address) {
                                used_space
                                free_space
                                size
                                status
                                type
                                vdisk_count
                                file_count
                                iso_count
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


