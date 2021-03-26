import { CUSTOM_ELEMENTS_SCHEMA } from '@angular/core';
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { of } from 'rxjs';

import { ResourcePoolsComponent } from './resource_pools.component';
import { ResourcePoolsService } from './resource_pools.service';

describe('ResourcePoolsComponent', () => {
  let component: ResourcePoolsComponent;
  let fixture: ComponentFixture<ResourcePoolsComponent>;

  let serviceStub: Partial<ResourcePoolsService>;

  beforeEach(async(() => {
    serviceStub = {
      getAllResourcePools(): any {
        return {
          valueChanges: of({
            data: {
              resource_pools: []
            }
          })
        };
      },
      paramsForGetResourcePools: {
        spin: false
      }
    };

    TestBed.configureTestingModule({
      imports: [ RouterTestingModule ],
      declarations: [ ResourcePoolsComponent ],
      providers: [
        {
          provide: ResourcePoolsService,
          useValue: serviceStub
        },
      ],
      schemas: [
        CUSTOM_ELEMENTS_SCHEMA
      ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ResourcePoolsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
