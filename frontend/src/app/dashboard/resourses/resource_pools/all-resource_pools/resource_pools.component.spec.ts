import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ResourcePoolsComponent } from './resource_pools.component';

describe('TemplatesComponent', () => {
  let component: ResourcePoolsComponent;
  let fixture: ComponentFixture<ResourcePoolsComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ResourcePoolsComponent ]
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
